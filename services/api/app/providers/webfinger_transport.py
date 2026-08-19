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

from ..network_metadata import resolve_public_host_ips
from .errors import (
    ProviderExecutionError,
    ProviderPolicyError,
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderTransientError,
)
from .webfinger_admission import (
    WebFingerAdmissionError,
    webfinger_network_target,
    webfinger_request_target,
)

_MAX_RESPONSE_BYTES = 64 * 1024
_MAX_REDIRECTS = 3
_TIMEOUT_SECONDS = 4.0


@dataclass(frozen=True, slots=True)
class PinnedHTTPSResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


Resolver = Callable[[str], Awaitable[tuple[str, ...]]]
PinnedRequester = Callable[[str, str, str], Awaitable[PinnedHTTPSResponse]]


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPSConnection that pins TCP to a reviewed IP while validating the DNS host."""

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
                "Accept": "application/jrd+json, application/json;q=0.8",
                "User-Agent": "PersonaLattice/0.0.1 webfinger-research",
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
                    "WebFinger response used an invalid Content-Length header."
                ) from exc
            if declared_size < 0 or declared_size > _MAX_RESPONSE_BYTES:
                raise ProviderResultValidationError(
                    "WebFinger response exceeded the adapter size limit."
                )
        body = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(body) > _MAX_RESPONSE_BYTES:
            raise ProviderResultValidationError(
                "WebFinger response exceeded the adapter size limit."
            )
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


def _validated_public_addresses(addresses: tuple[str, ...]) -> tuple[str, ...]:
    if not addresses:
        return ()
    admitted: list[str] = []
    for raw in addresses:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError as exc:
            raise ProviderPolicyError(
                "WebFinger DNS admission returned a malformed address."
            ) from exc
        if not address.is_global:
            raise ProviderPolicyError(
                "WebFinger DNS admission refused a non-global address."
            )
        value = address.compressed
        if value not in admitted:
            admitted.append(value)
    return tuple(admitted[:8])


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
        raise ProviderResultValidationError("WebFinger returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("WebFinger returned an invalid JRD shape.")
    return payload


async def fetch_webfinger_jrd(
    profile_url: str,
    *,
    resolver: Resolver = resolve_public_host_ips,
    requester: PinnedRequester = pinned_https_request,
) -> dict[str, object] | None:
    """Fetch a WebFinger JRD through fresh DNS admission and IP-pinned HTTPS.

    This transport is intentionally not wired into the provider registry yet. It
    exists to prove the redirect/DNS/SSRF boundary before source activation.
    """

    request = webfinger_request_target(profile_url)
    current_url = request.endpoint
    contacted_provider = False

    for redirect_index in range(_MAX_REDIRECTS + 1):
        try:
            target = webfinger_network_target(current_url, allow_query=True)
        except WebFingerAdmissionError as exc:
            if contacted_provider:
                raise ProviderResultValidationError(str(exc)) from exc
            raise ProviderPolicyError(str(exc)) from exc

        addresses = _validated_public_addresses(await resolver(target.hostname))
        if not addresses:
            if contacted_provider:
                raise ProviderResultValidationError(
                    "WebFinger redirect target did not resolve to a globally routable address."
                )
            raise ProviderPolicyError(
                "WebFinger target did not resolve to a globally routable address."
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
            raise ProviderTransientError("WebFinger HTTPS request failed.") from last_network_error

        contacted_provider = True
        status = response.status
        if status == 404:
            return None
        if status == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(response.headers))
        if status in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("WebFinger service was unavailable.")
        if 300 <= status < 400:
            location = response.headers.get("location")
            if location is None:
                raise ProviderResultValidationError(
                    "WebFinger redirect response omitted the Location header."
                )
            if redirect_index >= _MAX_REDIRECTS:
                raise ProviderResultValidationError("WebFinger exceeded the redirect limit.")
            try:
                redirect = webfinger_network_target(location, allow_query=True)
            except WebFingerAdmissionError as exc:
                raise ProviderResultValidationError(str(exc)) from exc
            current_url = redirect.url
            continue
        if status != 200:
            raise ProviderExecutionError(f"WebFinger request returned HTTP {status}.")

        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        if content_type not in {"application/jrd+json", "application/json"}:
            raise ProviderResultValidationError(
                "WebFinger response used an unsupported media type."
            )
        return _json_object(response.body)

    raise AssertionError("WebFinger redirect loop escaped its bounded iteration.")