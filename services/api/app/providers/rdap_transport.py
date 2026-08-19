# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
import http.client
import ipaddress
import json
import socket
import ssl
from urllib.parse import urljoin, urlsplit, urlunsplit

from ..network_metadata import resolve_public_host_ips
from .errors import (
    ProviderExecutionError,
    ProviderPolicyError,
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderTransientError,
)
from .rdap_admission import (
    RdapAdmissionError,
    rdap_bootstrap_base_urls,
    rdap_domain_query_url,
)

_MAX_RESPONSE_BYTES = 64 * 1024
_MAX_REDIRECTS = 3
_MAX_RESOLVED_ADDRESSES = 8
_TIMEOUT_SECONDS = 4.0


@dataclass(frozen=True, slots=True)
class PinnedHTTPSResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True, slots=True)
class RdapDomainFetchResult:
    payload: dict[str, object]
    canonical_query_url: str
    response_url: str


@dataclass(frozen=True, slots=True)
class RdapNetworkTarget:
    url: str
    hostname: str
    request_target: str


Resolver = Callable[[str], Awaitable[tuple[str, ...]]]
PinnedRequester = Callable[[str, str, str], Awaitable[PinnedHTTPSResponse]]


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Pin TCP to one admitted address while retaining hostname TLS verification."""

    def __init__(self, hostname: str, connect_ip: str) -> None:
        super().__init__(
            hostname,
            port=443,
            timeout=_TIMEOUT_SECONDS,
            context=ssl.create_default_context(),
        )
        self._connect_ip = connect_ip

    def connect(self) -> None:
        sock = socket.create_connection(
            (self._connect_ip, self.port),
            self.timeout,
            self.source_address,
        )
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


def _pinned_https_request_sync(
    hostname: str,
    connect_ip: str,
    request_target: str,
) -> PinnedHTTPSResponse:
    connection = _PinnedHTTPSConnection(hostname, connect_ip)
    try:
        connection.request(
            "GET",
            request_target,
            headers={
                "Accept": "application/rdap+json",
                "User-Agent": "PersonaLattice/0.0.1 rdap-research",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        content_length = response.getheader("Content-Length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError as exc:
                raise ProviderResultValidationError(
                    "RDAP response used an invalid Content-Length header."
                ) from exc
            if declared_size < 0 or declared_size > _MAX_RESPONSE_BYTES:
                raise ProviderResultValidationError("RDAP response exceeded the adapter size limit.")
        body = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(body) > _MAX_RESPONSE_BYTES:
            raise ProviderResultValidationError("RDAP response exceeded the adapter size limit.")
        headers = {key.casefold(): value for key, value in response.getheaders()}
        return PinnedHTTPSResponse(status=response.status, headers=headers, body=body)
    finally:
        connection.close()


async def pinned_https_request(
    hostname: str,
    connect_ip: str,
    request_target: str,
) -> PinnedHTTPSResponse:
    return await asyncio.to_thread(
        _pinned_https_request_sync,
        hostname,
        connect_ip,
        request_target,
    )


def _network_target(value: str) -> RdapNetworkTarget:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise ProviderPolicyError("RDAP network target is missing or exceeds limits.")
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value):
        raise ProviderPolicyError("RDAP network target contains whitespace or control characters.")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname is None:
        raise ProviderPolicyError("RDAP network target must use HTTPS with a DNS hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise ProviderPolicyError("RDAP network target must not contain credentials.")
    if parsed.fragment:
        raise ProviderPolicyError("RDAP network target must not contain a fragment.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ProviderPolicyError("RDAP network target has an invalid port.") from exc
    if port not in {None, 443}:
        raise ProviderPolicyError("RDAP network target may use only the default HTTPS port.")

    hostname = parsed.hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ProviderPolicyError("RDAP network target must use a DNS hostname, not an IP literal.")
    try:
        hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ProviderPolicyError("RDAP network target hostname is not valid IDNA.") from exc
    labels = hostname.split(".")
    if len(labels) < 2 or hostname.endswith((".local", ".localhost", ".internal", ".home", ".lan")):
        raise ProviderPolicyError("RDAP network target hostname is not a public DNS-style name.")
    if any(
        not label
        or len(label) > 63
        or not label[0].isalnum()
        or not label[-1].isalnum()
        or any(not (character.isalnum() or character == "-") for character in label)
        for label in labels
    ):
        raise ProviderPolicyError("RDAP network target hostname contains an invalid DNS label.")

    path = parsed.path or "/"
    request_target = path + (f"?{parsed.query}" if parsed.query else "")
    normalized_url = urlunsplit(("https", hostname, path, parsed.query, ""))
    return RdapNetworkTarget(
        url=normalized_url,
        hostname=hostname,
        request_target=request_target,
    )


def _validated_public_addresses(addresses: tuple[str, ...]) -> tuple[str, ...]:
    if len(addresses) > _MAX_RESOLVED_ADDRESSES:
        raise ProviderPolicyError("RDAP DNS admission returned too many addresses.")
    admitted: list[str] = []
    for raw in addresses:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError as exc:
            raise ProviderPolicyError("RDAP DNS admission returned a malformed address.") from exc
        if not address.is_global:
            raise ProviderPolicyError("RDAP DNS admission refused a non-global address.")
        value = address.compressed
        if value not in admitted:
            admitted.append(value)
    return tuple(admitted)


def _retry_after(headers: Mapping[str, str]) -> float | None:
    raw = headers.get("retry-after")
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _json_object(body: bytes) -> dict[str, object]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("RDAP returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("RDAP returned an invalid object shape.")
    return payload


async def _request_one_rdap_url(
    query_url: str,
    *,
    resolver: Resolver,
    requester: PinnedRequester,
) -> RdapDomainFetchResult | None:
    canonical_query = _network_target(query_url).url
    current_url = canonical_query
    contacted_provider = False

    for redirect_index in range(_MAX_REDIRECTS + 1):
        try:
            target = _network_target(current_url)
        except ProviderPolicyError as exc:
            if contacted_provider:
                raise ProviderResultValidationError(str(exc)) from exc
            raise

        addresses = _validated_public_addresses(await resolver(target.hostname))
        if not addresses:
            if contacted_provider:
                raise ProviderResultValidationError(
                    "RDAP redirect target did not resolve to a globally routable address."
                )
            raise ProviderPolicyError(
                "RDAP target did not resolve to a globally routable address."
            )

        response: PinnedHTTPSResponse | None = None
        last_network_error: BaseException | None = None
        for address in addresses:
            try:
                response = await requester(target.hostname, address, target.request_target)
            except ProviderResultValidationError:
                raise
            except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException) as exc:
                last_network_error = exc
                continue
            break
        if response is None:
            raise ProviderTransientError("RDAP HTTPS request failed.") from last_network_error

        contacted_provider = True
        status = response.status
        if status == 404:
            return None
        if status == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(response.headers))
        if status in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("RDAP service was unavailable.")
        if 300 <= status < 400:
            location = response.headers.get("location")
            if location is None:
                raise ProviderResultValidationError("RDAP redirect response omitted the Location header.")
            if redirect_index >= _MAX_REDIRECTS:
                raise ProviderResultValidationError("RDAP exceeded the redirect limit.")
            redirect_url = urljoin(target.url, location)
            try:
                current_url = _network_target(redirect_url).url
            except ProviderPolicyError as exc:
                raise ProviderResultValidationError(str(exc)) from exc
            continue
        if status != 200:
            raise ProviderExecutionError(f"RDAP request returned HTTP {status}.")

        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        if content_type != "application/rdap+json":
            raise ProviderResultValidationError("RDAP response used an unsupported media type.")
        return RdapDomainFetchResult(
            payload=_json_object(response.body),
            canonical_query_url=canonical_query,
            response_url=target.url,
        )

    raise AssertionError("RDAP redirect loop escaped its bounded iteration.")


async def fetch_rdap_domain(
    domain: str,
    *,
    bootstrap_payload: Mapping[str, object],
    resolver: Resolver = resolve_public_host_ips,
    requester: PinnedRequester = pinned_https_request,
) -> RdapDomainFetchResult | None:
    """Fetch one domain from IANA-bootstrap-selected RDAP services safely.

    The IANA bootstrap document is supplied by the caller so this transport does
    not fetch it for every research request. It tries equivalent authoritative
    base URLs in registry order only when a service is transiently unavailable.
    RDAP remains unbound/non-executable until a later governed activation block.
    """

    try:
        base_urls = rdap_bootstrap_base_urls(bootstrap_payload, domain=domain)
        query_urls = tuple(rdap_domain_query_url(base, domain=domain) for base in base_urls)
    except RdapAdmissionError as exc:
        raise ProviderPolicyError(str(exc)) from exc

    last_transient: ProviderTransientError | None = None
    for query_url in query_urls:
        try:
            return await _request_one_rdap_url(
                query_url,
                resolver=resolver,
                requester=requester,
            )
        except ProviderTransientError as exc:
            last_transient = exc
            continue
    if last_transient is not None:
        raise last_transient
    raise AssertionError("RDAP bootstrap produced no query URL.")
