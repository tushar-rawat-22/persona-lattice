# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_WAYBACK_AVAILABILITY_ENDPOINT = "https://archive.org/wayback/available"
_USER_AGENT = "PersonaLattice/0.0.1 wayback-availability-research"
_MAX_RAW_RESPONSE_BYTES = 32 * 1024
_TIMESTAMP_RE = re.compile(r"^[0-9]{14}$")
_STATUS_RE = re.compile(r"^[1-5][0-9]{2}$")

WaybackFetch = Callable[[str], Awaitable[dict[str, object]]]


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_wayback_availability_sync(url: str) -> dict[str, object]:
    request_url = f"{_WAYBACK_AVAILABILITY_ENDPOINT}?{urlencode({'url': url})}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("Wayback availability endpoint was unavailable.") from exc
        raise ProviderExecutionError("Wayback availability request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Wayback availability request failed.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResultValidationError("Wayback availability response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Wayback availability endpoint returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("Wayback availability endpoint returned an invalid response shape.")
    return payload


async def fetch_wayback_availability(url: str) -> dict[str, object]:
    return await asyncio.to_thread(_fetch_wayback_availability_sync, url)


def _validated_snapshot_locator(value: object, *, timestamp: str) -> str:
    if not isinstance(value, str):
        raise ProviderResultValidationError("Wayback capture is missing its snapshot locator.")
    parts = urlsplit(value)
    if (
        parts.scheme not in {"http", "https"}
        or parts.hostname is None
        or parts.hostname.casefold() != "web.archive.org"
        or parts.username is not None
        or parts.password is not None
        or not parts.path.startswith(f"/web/{timestamp}/")
    ):
        raise ProviderResultValidationError("Wayback capture returned an invalid snapshot locator.")
    return value


def _capture_from_payload(payload: dict[str, object]) -> dict[str, object] | None:
    snapshots = payload.get("archived_snapshots")
    if not isinstance(snapshots, dict):
        raise ProviderResultValidationError("Wayback response is missing archived_snapshots.")
    if not snapshots:
        return None

    closest = snapshots.get("closest")
    if not isinstance(closest, dict):
        raise ProviderResultValidationError("Wayback response has an invalid closest snapshot.")
    available = closest.get("available")
    if available is False:
        return None
    if available is not True:
        raise ProviderResultValidationError("Wayback response has an invalid availability flag.")

    status = closest.get("status")
    timestamp = closest.get("timestamp")
    if not isinstance(status, str) or _STATUS_RE.fullmatch(status) is None:
        raise ProviderResultValidationError("Wayback capture has an invalid HTTP status.")
    if not isinstance(timestamp, str) or _TIMESTAMP_RE.fullmatch(timestamp) is None:
        raise ProviderResultValidationError("Wayback capture has an invalid timestamp.")
    locator = _validated_snapshot_locator(closest.get("url"), timestamp=timestamp)
    return {
        "capture_available": True,
        "capture_status": status,
        "capture_timestamp": timestamp,
        "snapshot_locator": locator,
    }


class WaybackAvailabilityProvider:
    descriptor = PROVIDER_BY_NAME["wayback_url_availability"]

    def __init__(self, *, fetcher: WaybackFetch = fetch_wayback_availability) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Wayback availability lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("Wayback availability lookup only accepts URLs.")

        parts = urlsplit(query.identifier_value)
        if parts.scheme not in {"http", "https"} or parts.hostname is None:
            raise ProviderValidationError("Wayback availability lookup requires a canonical public URL.")

        payload = await self.fetcher(query.identifier_value)
        capture = _capture_from_payload(payload)
        if capture is None:
            return ProviderResult(observations=())

        source_locator = str(capture.pop("snapshot_locator"))
        details = {
            "queried_url": query.identifier_value,
            **capture,
            "archived_content_fetched": False,
            "identity_claim": False,
        }
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=source_locator,
                    payload=details,
                ),
            )
        )
