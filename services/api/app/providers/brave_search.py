# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..public_search import PublicSearchResult, _decode_results, _exact_query
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


_BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
_MAX_RESULTS = 10
_MAX_RAW_RESPONSE_BYTES = 256 * 1024


BraveFetch = Callable[[str, str], Awaitable[tuple[PublicSearchResult, ...]]]


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_brave_results_sync(identifier: str, secret: str) -> tuple[PublicSearchResult, ...]:
    query = urlencode(
        {
            "q": _exact_query(identifier),
            "count": str(_MAX_RESULTS),
            "safesearch": "moderate",
            "text_decorations": "false",
            "result_filter": "web",
        }
    )
    request = Request(
        f"{_BRAVE_SEARCH_ENDPOINT}?{query}",
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": secret,
            "User-Agent": "PersonaLattice/0.0.1 private-public-evidence-research",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=5.0) as response:
            raw = response.read(_MAX_RAW_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("Brave public search was unavailable.") from exc
        raise ProviderExecutionError("Brave public search rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Brave public search was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("Brave public search response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Brave public search returned invalid JSON.") from exc
    try:
        return _decode_results(payload)
    except RuntimeError as exc:
        raise ProviderResultValidationError("Brave public search returned an invalid result shape.") from exc


async def fetch_brave_results(identifier: str, secret: str) -> tuple[PublicSearchResult, ...]:
    return await asyncio.to_thread(_fetch_brave_results_sync, identifier, secret)


class BravePublicWebSearchProvider:
    descriptor = PROVIDER_BY_NAME["brave_public_web_index"]

    def __init__(self, *, fetcher: BraveFetch = fetch_brave_results) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is None or not secret.strip():
            raise ProviderValidationError("Brave public search requires a server-side API key.")
        if query.identifier_kind not in self.descriptor.supported_identifier_kinds:
            raise ProviderValidationError("Brave public search does not support this identifier kind.")

        results = await self.fetcher(query.identifier_value, secret)
        return ProviderResult(
            observations=tuple(
                ProviderObservationData(
                    source_locator=result.url,
                    payload={
                        "title": result.title,
                        "description": result.description,
                        "exact_identifier_query": True,
                        "content_fetched": False,
                        "identity_claim": False,
                    },
                )
                for result in results
            )
        )
