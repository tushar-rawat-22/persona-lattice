# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import gzip
from io import BytesIO
import json
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


_API_ROOT = "https://api.stackexchange.com/2.3/users"
_USER_AGENT = "PersonaLattice/0.0.1 stack-overflow-profile-research"
_MAX_RAW_RESPONSE_BYTES = 32 * 1024

StackOverflowFetch = Callable[[int], Awaitable[dict[str, object]]]


def stack_overflow_user_id_from_url(value: str) -> int | None:
    """Return the exact Stack Overflow user id carried by a profile URL.

    This intentionally does not recognize search pages, display names, other
    Stack Exchange sites or arbitrary Stack Overflow paths. A provider call is
    only justified when the supplied URL itself identifies one numeric account.
    """

    parts = urlsplit(value)
    if (
        parts.scheme not in {"http", "https"}
        or parts.hostname is None
        or parts.hostname.casefold() != "stackoverflow.com"
        or parts.username is not None
        or parts.password is not None
        or parts.port not in {None, 80, 443}
    ):
        return None

    segments = [segment for segment in parts.path.split("/") if segment]
    if len(segments) not in {2, 3} or segments[0] != "users":
        return None
    if not segments[1].isdigit():
        return None
    user_id = int(segments[1])
    if user_id <= 0:
        return None
    return user_id


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _bounded_gzip_decode(raw: bytes) -> bytes:
    try:
        with gzip.GzipFile(fileobj=BytesIO(raw)) as stream:
            decoded = stream.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except (OSError, EOFError) as exc:
        raise ProviderResultValidationError("Stack Exchange API returned invalid gzip data.") from exc
    if len(decoded) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResultValidationError("Stack Exchange API response exceeded the adapter limit.")
    return decoded


def _fetch_stack_overflow_profile_sync(user_id: int) -> dict[str, object]:
    request_url = f"{_API_ROOT}/{user_id}?{urlencode({'site': 'stackoverflow'})}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip, identity",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
            content_encoding = (response.headers.get("Content-Encoding") or "").casefold()
    except HTTPError as exc:
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("Stack Exchange API was unavailable.") from exc
        raise ProviderExecutionError("Stack Exchange API request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Stack Exchange API request failed.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResultValidationError("Stack Exchange API response exceeded the adapter limit.")
    if content_encoding == "gzip":
        raw = _bounded_gzip_decode(raw)
    elif content_encoding not in {"", "identity"}:
        raise ProviderResultValidationError("Stack Exchange API returned an unsupported content encoding.")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Stack Exchange API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("Stack Exchange API returned an invalid response shape.")
    return payload


async def fetch_stack_overflow_profile(user_id: int) -> dict[str, object]:
    return await asyncio.to_thread(_fetch_stack_overflow_profile_sync, user_id)


def _bounded_nonnegative_int(payload: dict[str, object], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProviderResultValidationError(f"Stack Overflow profile has an invalid {field}.")
    return value


def _validated_profile_link(value: object, *, user_id: int) -> str:
    if not isinstance(value, str):
        raise ProviderResultValidationError("Stack Overflow profile is missing its canonical link.")
    returned_id = stack_overflow_user_id_from_url(value)
    parts = urlsplit(value)
    if parts.scheme != "https" or returned_id != user_id:
        raise ProviderResultValidationError("Stack Overflow profile returned an invalid canonical link.")
    return value


def _profile_from_payload(payload: dict[str, object], *, expected_user_id: int) -> dict[str, object] | None:
    backoff = payload.get("backoff")
    if backoff is not None:
        if isinstance(backoff, bool) or not isinstance(backoff, int) or backoff < 0:
            raise ProviderResultValidationError("Stack Exchange API returned an invalid backoff value.")
        raise ProviderRemoteRateLimitError(retry_after=float(backoff))

    items = payload.get("items")
    if not isinstance(items, list):
        raise ProviderResultValidationError("Stack Exchange API response is missing items.")
    if not items:
        return None
    if len(items) != 1 or not isinstance(items[0], dict):
        raise ProviderResultValidationError("Stack Exchange API returned an invalid exact-user result.")

    item = items[0]
    user_id = _bounded_nonnegative_int(item, "user_id")
    if user_id != expected_user_id or user_id == 0:
        raise ProviderResultValidationError("Stack Exchange API returned a different user id.")
    display_name = item.get("display_name")
    if not isinstance(display_name, str) or not display_name.strip():
        raise ProviderResultValidationError("Stack Overflow profile has an invalid display_name.")
    reputation = _bounded_nonnegative_int(item, "reputation")
    creation_date = _bounded_nonnegative_int(item, "creation_date")
    link = _validated_profile_link(item.get("link"), user_id=user_id)

    return {
        "source_locator": link,
        "stack_overflow_user_id": user_id,
        "stack_overflow_display_name": display_name,
        "stack_overflow_reputation": reputation,
        "stack_overflow_creation_unix": creation_date,
        "api_attribution": "Stack Overflow",
        "identity_claim": False,
    }


class StackOverflowPublicProfileProvider:
    descriptor = PROVIDER_BY_NAME["stack_overflow_public_profile"]

    def __init__(self, *, fetcher: StackOverflowFetch = fetch_stack_overflow_profile) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Stack Overflow profile lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("Stack Overflow profile lookup only accepts URLs.")

        user_id = stack_overflow_user_id_from_url(query.identifier_value)
        if user_id is None:
            raise ProviderValidationError("Stack Overflow profile lookup requires an exact profile URL.")

        payload = await self.fetcher(user_id)
        profile = _profile_from_payload(payload, expected_user_id=user_id)
        if profile is None:
            return ProviderResult(observations=())

        source_locator = str(profile.pop("source_locator"))
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=source_locator,
                    payload=profile,
                ),
            )
        )
