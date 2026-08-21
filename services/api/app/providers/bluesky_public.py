# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .bluesky_admission import (
    BlueskyAdmissionError,
    BlueskyPublicWebOptOut,
    admitted_bluesky_profile_fields,
    normalize_bluesky_handle,
)
from .errors import (
    ProviderAccountUnavailableError,
    ProviderExecutionError,
    ProviderPublicWebOptOutError,
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_MAX_RAW_RESPONSE_BYTES = 64 * 1024
_PROFILE_ENDPOINT = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile"


BlueskyFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _error_payload(exc: HTTPError) -> dict[str, object] | None:
    try:
        raw = exc.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except OSError:
        return None
    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _fetch_bluesky_public_profile_sync(handle: str) -> dict[str, object] | None:
    normalized = normalize_bluesky_handle(handle)
    request = Request(
        f"{_PROFILE_ENDPOINT}?{urlencode({'actor': normalized})}",
        headers={
            "Accept": "application/json",
            "User-Agent": "PersonaLattice/0.0.1 public-profile-research",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        payload = _error_payload(exc)
        error = payload.get("error") if payload is not None else None
        message = payload.get("message") if payload is not None else None
        if exc.code == 400 and message == "Profile not found":
            return None
        if exc.code == 400 and error in {"AccountTakedown", "AccountDeactivated"}:
            raise ProviderAccountUnavailableError("Bluesky account is not publicly available.") from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("Bluesky public AppView was unavailable.") from exc
        raise ProviderExecutionError("Bluesky public profile request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Bluesky public profile request failed.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResultValidationError("Bluesky public profile response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Bluesky public profile returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("Bluesky public profile returned an invalid response shape.")
    return payload


async def fetch_bluesky_public_profile(handle: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_bluesky_public_profile_sync, handle)


def bluesky_profile_handle_from_url(value: str) -> str | None:
    """Return the normalized handle from an exact canonical Bluesky profile URL."""

    parts = urlsplit(value)
    try:
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "bsky.app"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
    ):
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    if len(segments) != 2 or segments[0] != "profile":
        return None
    raw_handle = segments[1]
    if parts.path != f"/profile/{raw_handle}" or "%" in raw_handle:
        return None
    if raw_handle.startswith("did:"):
        return None
    try:
        handle = normalize_bluesky_handle(raw_handle)
    except BlueskyAdmissionError:
        return None
    if raw_handle != handle:
        return None
    return handle


class BlueskyPublicProfileProvider:
    descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]

    def __init__(self, *, fetcher: BlueskyFetch = fetch_bluesky_public_profile) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Bluesky public profile lookup does not accept credentials.")
        if query.identifier_kind == "username":
            try:
                handle = normalize_bluesky_handle(query.identifier_value)
            except BlueskyAdmissionError as exc:
                raise ProviderValidationError(str(exc)) from exc
        elif query.identifier_kind == "url":
            handle = bluesky_profile_handle_from_url(query.identifier_value)
            if handle is None:
                raise ProviderValidationError(
                    "Bluesky URL lookup requires an exact canonical handle profile URL."
                )
        else:
            raise ProviderValidationError(
                "Bluesky public profile lookup only accepts reviewed handles or exact handle profile URLs."
            )

        payload = await self.fetcher(handle)
        if payload is None:
            return ProviderResult(observations=())
        try:
            details = admitted_bluesky_profile_fields(payload, requested_handle=handle)
        except BlueskyPublicWebOptOut as exc:
            raise ProviderPublicWebOptOutError(
                "Bluesky profile opted out of unauthenticated public-web use."
            ) from exc
        except BlueskyAdmissionError as exc:
            raise ProviderResultValidationError(str(exc)) from exc

        source_locator = f"https://bsky.app/profile/{quote(handle, safe='.-')}"
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=source_locator,
                    payload=details,
                ),
            )
        )
