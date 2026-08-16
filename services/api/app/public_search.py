# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .providers.rate_limit import RateBudget


BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
_MAX_QUERY_CHARS = 300
_MAX_RESULTS = 10
_MAX_RESPONSE_BYTES = 256 * 1024
_TIMEOUT_SECONDS = 5.0
_RESULT_TEXT_CHARS = 600
_SEARCH_BUDGET = RateBudget(limit=10, window_seconds=60.0)


@dataclass(frozen=True, slots=True)
class PublicSearchResult:
    title: str
    url: str
    description: str


def _api_key() -> str | None:
    value = os.environ.get("PERSONALATTICE_BRAVE_SEARCH_API_KEY", "").strip()
    return value or None


def public_search_configured() -> bool:
    return _api_key() is not None


def _bounded_text(value: object, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _canonical_public_result_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value.strip())
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return None
        if parts.username or parts.password:
            return None
        port = parts.port
    except ValueError:
        return None
    hostname = parts.hostname.lower()
    if port is not None and not (
        (parts.scheme.lower() == "https" and port == 443)
        or (parts.scheme.lower() == "http" and port == 80)
    ):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


def _exact_query(identifier: str) -> str:
    compact = " ".join(identifier.strip().split())
    if not compact:
        raise ValueError("public search identifier is empty")
    escaped = compact.replace('"', "")[: _MAX_QUERY_CHARS - 2]
    return f'"{escaped}"'


def _decode_results(payload: object) -> tuple[PublicSearchResult, ...]:
    if not isinstance(payload, dict):
        raise RuntimeError("Public search returned an invalid response shape.")
    web = payload.get("web")
    if web is None:
        return ()
    if not isinstance(web, dict):
        raise RuntimeError("Public search returned an invalid web result container.")
    rows = web.get("results")
    if rows is None:
        return ()
    if not isinstance(rows, list):
        raise RuntimeError("Public search returned an invalid result list.")

    results: list[PublicSearchResult] = []
    seen: set[str] = set()
    for row in rows[:_MAX_RESULTS]:
        if not isinstance(row, dict):
            continue
        url = _canonical_public_result_url(row.get("url"))
        if url is None or url in seen:
            continue
        seen.add(url)
        results.append(
            PublicSearchResult(
                title=_bounded_text(row.get("title"), limit=200),
                url=url,
                description=_bounded_text(row.get("description"), limit=_RESULT_TEXT_CHARS),
            )
        )
    return tuple(results)


def _search_sync(identifier: str, api_key: str) -> tuple[PublicSearchResult, ...]:
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
        f"{BRAVE_SEARCH_ENDPOINT}?{query}",
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
            "User-Agent": "PersonaLattice/0.0.1 private-public-evidence-research",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise RuntimeError("Public search provider rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Public search provider was unavailable.") from exc

    if len(raw) > _MAX_RESPONSE_BYTES:
        raise RuntimeError("Public search response exceeded the configured limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Public search returned invalid JSON.") from exc
    return _decode_results(payload)


async def search_exact_public_mentions(identifier: str) -> tuple[PublicSearchResult, ...]:
    """Search a licensed public web index for an exact identifier mention.

    This is discovery evidence only. Results are not fetched automatically and
    snippets are not converted into identity claims or hidden/private data.
    """

    key = _api_key()
    if key is None:
        return ()
    _SEARCH_BUDGET.consume()
    return await asyncio.to_thread(_search_sync, identifier, key)
