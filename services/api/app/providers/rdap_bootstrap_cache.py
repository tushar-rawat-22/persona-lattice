# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import http.client
import json
import ssl

_IANA_RDAP_HOST = "data.iana.org"
_IANA_RDAP_PATH = "/rdap/dns.json"
IANA_RDAP_DNS_BOOTSTRAP_URL = f"https://{_IANA_RDAP_HOST}{_IANA_RDAP_PATH}"
_MAX_RESPONSE_BYTES = 128 * 1024
_TIMEOUT_SECONDS = 4.0
_DEFAULT_TTL = timedelta(hours=24)
_MAX_TTL = timedelta(days=7)
_MAX_BOOTSTRAP_SERVICES = 512
_MAX_BASE_URLS_PER_SERVICE = 8


class RdapBootstrapUnavailableError(RuntimeError):
    """The fixed IANA bootstrap authority could not be refreshed."""


class RdapBootstrapValidationError(ValueError):
    """The fixed IANA bootstrap authority returned an unusable response."""


@dataclass(frozen=True, slots=True)
class RdapBootstrapHTTPResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True, slots=True)
class RdapBootstrapSnapshot:
    payload: dict[str, object]
    fetched_at: datetime
    expires_at: datetime
    etag: str | None = None
    last_modified: str | None = None


BootstrapFetcher = Callable[[Mapping[str, str]], Awaitable[RdapBootstrapHTTPResponse]]


def _utc(value: datetime | None = None) -> datetime:
    resolved = value or datetime.now(timezone.utc)
    if resolved.tzinfo is None:
        raise ValueError("RDAP bootstrap cache timestamps must be timezone-aware.")
    return resolved.astimezone(timezone.utc)


def _fetch_iana_bootstrap_sync(headers: Mapping[str, str]) -> RdapBootstrapHTTPResponse:
    connection = http.client.HTTPSConnection(
        _IANA_RDAP_HOST,
        port=443,
        timeout=_TIMEOUT_SECONDS,
        context=ssl.create_default_context(),
    )
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "PersonaLattice/0.0.1 rdap-bootstrap-cache",
        "Connection": "close",
        **dict(headers),
    }
    try:
        connection.request("GET", _IANA_RDAP_PATH, headers=request_headers)
        response = connection.getresponse()
        content_length = response.getheader("Content-Length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError as exc:
                raise RdapBootstrapValidationError(
                    "IANA RDAP bootstrap used an invalid Content-Length header."
                ) from exc
            if declared_size < 0 or declared_size > _MAX_RESPONSE_BYTES:
                raise RdapBootstrapValidationError(
                    "IANA RDAP bootstrap exceeded the response-size limit."
                )
        body = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(body) > _MAX_RESPONSE_BYTES:
            raise RdapBootstrapValidationError(
                "IANA RDAP bootstrap exceeded the response-size limit."
            )
        return RdapBootstrapHTTPResponse(
            status=response.status,
            headers={key.casefold(): value for key, value in response.getheaders()},
            body=body,
        )
    except RdapBootstrapValidationError:
        raise
    except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException) as exc:
        raise RdapBootstrapUnavailableError("IANA RDAP bootstrap request failed.") from exc
    finally:
        connection.close()


async def fetch_iana_rdap_dns_bootstrap(
    headers: Mapping[str, str],
) -> RdapBootstrapHTTPResponse:
    """Fetch the fixed IANA DNS bootstrap document without following redirects."""

    return await asyncio.to_thread(_fetch_iana_bootstrap_sync, headers)


def _bounded_payload(body: bytes) -> dict[str, object]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RdapBootstrapValidationError("IANA RDAP bootstrap returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise RdapBootstrapValidationError("IANA RDAP bootstrap must be a JSON object.")
    services = payload.get("services")
    if not isinstance(services, Sequence) or isinstance(services, (str, bytes)):
        raise RdapBootstrapValidationError("IANA RDAP bootstrap requires a services array.")
    if not services or len(services) > _MAX_BOOTSTRAP_SERVICES:
        raise RdapBootstrapValidationError("IANA RDAP bootstrap service count is invalid.")
    for service in services:
        if not isinstance(service, Sequence) or isinstance(service, (str, bytes)) or len(service) != 2:
            raise RdapBootstrapValidationError(
                "IANA RDAP bootstrap service entries must contain DNS and URL arrays."
            )
        suffixes, urls = service
        if not isinstance(suffixes, Sequence) or isinstance(suffixes, (str, bytes)) or not suffixes:
            raise RdapBootstrapValidationError("IANA RDAP bootstrap DNS list is invalid.")
        if not isinstance(urls, Sequence) or isinstance(urls, (str, bytes)) or not urls:
            raise RdapBootstrapValidationError("IANA RDAP bootstrap URL list is invalid.")
        if len(urls) > _MAX_BASE_URLS_PER_SERVICE:
            raise RdapBootstrapValidationError("IANA RDAP bootstrap exposes too many base URLs.")
        if any(not isinstance(value, str) or not value for value in suffixes):
            raise RdapBootstrapValidationError("IANA RDAP bootstrap DNS entries must be strings.")
        if any(not isinstance(value, str) or not value for value in urls):
            raise RdapBootstrapValidationError("IANA RDAP bootstrap URLs must be strings.")
    return payload


def _cache_directives(headers: Mapping[str, str]) -> tuple[str, ...]:
    cache_control = headers.get("cache-control", "")
    return tuple(item.strip().casefold() for item in cache_control.split(",") if item.strip())


def _http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _cache_ttl(headers: Mapping[str, str], *, now: datetime) -> timedelta:
    directives = _cache_directives(headers)
    if "no-store" in directives or "no-cache" in directives:
        return timedelta(0)
    for directive in directives:
        if not directive.startswith("max-age="):
            continue
        raw = directive.split("=", 1)[1].strip().strip('"')
        try:
            seconds = int(raw)
        except ValueError:
            return timedelta(0)
        if seconds < 0:
            return timedelta(0)
        return min(timedelta(seconds=seconds), _MAX_TTL)

    expires_at = _http_date(headers.get("expires"))
    if expires_at is not None:
        date_at = _http_date(headers.get("date")) or now
        ttl = expires_at - date_at
        return min(max(ttl, timedelta(0)), _MAX_TTL)
    return _DEFAULT_TTL


class IanaRdapBootstrapCache:
    """Process-local, conditional-refresh cache for IANA's DNS RDAP registry.

    A fresh snapshot is reused without network I/O. Once expired, refresh is
    serialized through one lock and uses ETag/Last-Modified validators when the
    authority supplied them. Refresh failure never silently serves an expired
    snapshot; authoritative routing data fails closed instead.
    """

    def __init__(self, *, fetcher: BootstrapFetcher = fetch_iana_rdap_dns_bootstrap) -> None:
        self._fetcher = fetcher
        self._snapshot: RdapBootstrapSnapshot | None = None
        self._lock = asyncio.Lock()

    async def get_payload(self, *, now: datetime | None = None) -> dict[str, object]:
        current = _utc(now)
        snapshot = self._snapshot
        if snapshot is not None and current < snapshot.expires_at:
            return copy.deepcopy(snapshot.payload)

        async with self._lock:
            snapshot = self._snapshot
            if snapshot is not None and current < snapshot.expires_at:
                return copy.deepcopy(snapshot.payload)

            conditional_headers: dict[str, str] = {}
            if snapshot is not None and snapshot.etag:
                conditional_headers["If-None-Match"] = snapshot.etag
            if snapshot is not None and snapshot.last_modified:
                conditional_headers["If-Modified-Since"] = snapshot.last_modified

            response = await self._fetcher(conditional_headers)
            headers = {key.casefold(): value for key, value in response.headers.items()}
            directives = _cache_directives(headers)
            store_allowed = "no-store" not in directives
            ttl = _cache_ttl(headers, now=current)

            if response.status == 304:
                if snapshot is None:
                    raise RdapBootstrapValidationError(
                        "IANA RDAP bootstrap returned 304 without a cached snapshot."
                    )
                refreshed = RdapBootstrapSnapshot(
                    payload=snapshot.payload,
                    fetched_at=current,
                    expires_at=current + ttl,
                    etag=headers.get("etag", snapshot.etag),
                    last_modified=headers.get("last-modified", snapshot.last_modified),
                )
                self._snapshot = refreshed if store_allowed else None
                return copy.deepcopy(refreshed.payload)

            if response.status == 429 or response.status in {408, 500, 502, 503, 504}:
                raise RdapBootstrapUnavailableError(
                    f"IANA RDAP bootstrap was unavailable (HTTP {response.status})."
                )
            if 300 <= response.status < 400:
                raise RdapBootstrapValidationError(
                    "IANA RDAP bootstrap unexpectedly redirected; the fixed authority URL is required."
                )
            if response.status != 200:
                raise RdapBootstrapUnavailableError(
                    f"IANA RDAP bootstrap returned HTTP {response.status}."
                )

            content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
            if content_type != "application/json":
                raise RdapBootstrapValidationError(
                    "IANA RDAP bootstrap used an unsupported media type."
                )
            payload = _bounded_payload(response.body)
            refreshed = RdapBootstrapSnapshot(
                payload=payload,
                fetched_at=current,
                expires_at=current + ttl,
                etag=headers.get("etag"),
                last_modified=headers.get("last-modified"),
            )
            self._snapshot = refreshed if store_allowed else None
            return copy.deepcopy(payload)


IANA_RDAP_BOOTSTRAP_CACHE = IanaRdapBootstrapCache()
