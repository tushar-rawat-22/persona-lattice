# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_API_ROOT = "https://api.openalex.org/authors"
_USER_AGENT = "PersonaLattice/0.0.1 openalex-exact-author-research"
_MAX_RAW_RESPONSE_BYTES = 32 * 1024

OpenAlexFetch = Callable[[str, str], Awaitable[dict[str, object] | None]]


def openalex_author_id_from_url(value: str) -> str | None:
    """Return the exact OpenAlex author ID carried by a canonical author URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "openalex.org"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
    ):
        return None

    path = parts.path[:-1] if parts.path.endswith("/") and parts.path != "/" else parts.path
    if len(path) < 3 or not path.startswith("/A"):
        return None
    digits = path[2:]
    if not digits.isdigit() or int(digits) <= 0:
        return None
    return f"A{int(digits)}"


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_openalex_author_sync(author_id: str, secret: str) -> dict[str, object] | None:
    request_url = f"{_API_ROOT}/{author_id}?select=id,display_name,works_count,cited_by_count"
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {secret}",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=4.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("OpenAlex author API was unavailable.") from exc
        raise ProviderExecutionError("OpenAlex author API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("OpenAlex author API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("OpenAlex author API response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("OpenAlex author API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("OpenAlex author API returned an invalid response shape.")
    return payload


async def fetch_openalex_author(author_id: str, secret: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_openalex_author_sync, author_id, secret)


def _bounded_nonnegative_int(payload: dict[str, object], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProviderResultValidationError(f"OpenAlex author has an invalid {field}.")
    return value


def _profile_from_payload(payload: dict[str, object], *, expected_author_id: str) -> dict[str, object]:
    returned_id = payload.get("id")
    if not isinstance(returned_id, str):
        raise ProviderResultValidationError("OpenAlex author is missing its canonical id.")
    parsed_id = openalex_author_id_from_url(returned_id)
    if parsed_id != expected_author_id:
        raise ProviderResultValidationError("OpenAlex returned a different author id.")

    display_name = payload.get("display_name")
    if not isinstance(display_name, str) or not display_name.strip():
        raise ProviderResultValidationError("OpenAlex author has an invalid display_name.")

    return {
        "source_locator": f"https://openalex.org/{expected_author_id}",
        "openalex_author_id": expected_author_id,
        "openalex_display_name": display_name,
        "openalex_works_count": _bounded_nonnegative_int(payload, "works_count"),
        "openalex_cited_by_count": _bounded_nonnegative_int(payload, "cited_by_count"),
        "data_license": "CC0",
        "api_attribution": "OpenAlex",
        "identity_claim": False,
    }


class OpenAlexExactAuthorProvider:
    descriptor = PROVIDER_BY_NAME["openalex_exact_author"]

    def __init__(self, *, fetcher: OpenAlexFetch = fetch_openalex_author) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is None or not secret.strip():
            raise ProviderValidationError("OpenAlex exact-author lookup requires a server-side API key.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("OpenAlex exact-author lookup only accepts URLs.")

        author_id = openalex_author_id_from_url(query.identifier_value)
        if author_id is None:
            raise ProviderValidationError("OpenAlex exact-author lookup requires an exact author URL.")

        payload = await self.fetcher(author_id, secret)
        if payload is None:
            return ProviderResult(observations=())
        profile = _profile_from_payload(payload, expected_author_id=author_id)
        source_locator = str(profile.pop("source_locator"))
        return ProviderResult(
            observations=(
                ProviderObservationData(source_locator=source_locator, payload=profile),
            )
        )
