# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Callable
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..intelligence.sec_edgar_admission import sec_submissions_url
from .errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)


_MAX_RAW_RESPONSE_BYTES = 256 * 1024
_TIMEOUT_SECONDS = 4.0

OpenSecRequest = Callable[..., object]


def validate_sec_user_agent(value: str) -> str:
    """Validate the operator-supplied SEC identity header before any network request."""

    if not isinstance(value, str):
        raise ProviderValidationError("SEC EDGAR User-Agent must be configured explicitly.")
    text = value.strip()
    if text != value or len(text) < 8 or len(text) > 200:
        raise ProviderValidationError("SEC EDGAR User-Agent is invalid.")
    if "@" not in text or any(ord(character) < 32 or ord(character) == 127 for character in text):
        raise ProviderValidationError(
            "SEC EDGAR User-Agent must include a maintainable contact email address."
        )
    return text


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_sec_submissions_sync(
    cik: str,
    *,
    user_agent: str,
    opener: OpenSecRequest = urlopen,
) -> dict[str, object] | None:
    declared_user_agent = validate_sec_user_agent(user_agent)
    request = Request(
        sec_submissions_url(cik),
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": declared_user_agent,
        },
        method="GET",
    )
    try:
        response_context = opener(request, timeout=_TIMEOUT_SECONDS)
        with response_context as response:  # type: ignore[attr-defined]
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("SEC EDGAR submissions API was unavailable.") from exc
        raise ProviderExecutionError("SEC EDGAR submissions API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("SEC EDGAR submissions API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("SEC EDGAR submissions response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("SEC EDGAR submissions API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("SEC EDGAR submissions API returned an invalid response shape.")
    return payload


async def fetch_sec_submissions(cik: str, *, user_agent: str) -> dict[str, object] | None:
    """Fetch one exact SEC submissions object with no search, pagination or filing-body expansion."""

    return await asyncio.to_thread(
        _fetch_sec_submissions_sync,
        cik,
        user_agent=user_agent,
    )
