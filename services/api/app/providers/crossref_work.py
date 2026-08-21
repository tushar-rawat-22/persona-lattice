# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .doi import doi_from_canonical_url, validated_doi
from .errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_API_ROOT = "https://api.crossref.org/works"
_USER_AGENT = "PersonaLattice/0.0.1 crossref-exact-doi-research"
_MAX_RAW_RESPONSE_BYTES = 32 * 1024
_MAX_TITLE_LENGTH = 300
_MAX_AUTHOR_COUNT = 8
_MAX_AUTHOR_NAME_LENGTH = 120

CrossrefFetch = Callable[[str], Awaitable[dict[str, object] | None]]

# Compatibility/public provider helper retained for existing research/tests.
crossref_doi_from_url = doi_from_canonical_url


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_crossref_work_sync(doi: str) -> dict[str, object] | None:
    # Crossref's singleton examples encode the DOI as one path parameter,
    # including its slash. This also prevents DOI suffix punctuation becoming
    # query or fragment syntax.
    request_url = f"{_API_ROOT}/{quote(doi, safe='')}"
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
        if exc.code == 404:
            return None
        if exc.code == 429:
            raise ProviderRemoteRateLimitError(retry_after=_retry_after(exc)) from exc
        if exc.code in {408, 500, 502, 503, 504}:
            raise ProviderTransientError("Crossref REST API was unavailable.") from exc
        raise ProviderExecutionError("Crossref REST API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("Crossref REST API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("Crossref REST API response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("Crossref REST API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("Crossref REST API returned an invalid response shape.")
    return payload


async def fetch_crossref_work(doi: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_crossref_work_sync, doi)


def _bounded_text(value: object, *, field: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ProviderResultValidationError(f"Crossref work has an invalid {field}.")
    text = " ".join(value.split())
    if not text or len(text) > max_length:
        raise ProviderResultValidationError(f"Crossref work has an invalid {field}.")
    return text


def _title_from_message(message: dict[str, object]) -> str:
    titles = message.get("title")
    if not isinstance(titles, list) or not titles:
        raise ProviderResultValidationError("Crossref work is missing a title.")
    return _bounded_text(titles[0], field="title", max_length=_MAX_TITLE_LENGTH)


def _publication_year(message: dict[str, object]) -> int | None:
    for field in ("published-print", "published-online", "published", "issued"):
        date_value = message.get(field)
        if not isinstance(date_value, dict):
            continue
        date_parts = date_value.get("date-parts")
        if (
            not isinstance(date_parts, list)
            or not date_parts
            or not isinstance(date_parts[0], list)
            or not date_parts[0]
        ):
            continue
        year = date_parts[0][0]
        if isinstance(year, bool) or not isinstance(year, int) or year < 1000 or year > 9999:
            continue
        return year
    return None


def _author_names(message: dict[str, object]) -> tuple[str, ...]:
    authors = message.get("author")
    if authors is None:
        return ()
    if not isinstance(authors, list):
        raise ProviderResultValidationError("Crossref work has an invalid author list.")

    names: list[str] = []
    for author in authors[:_MAX_AUTHOR_COUNT]:
        if not isinstance(author, dict):
            raise ProviderResultValidationError("Crossref work has an invalid author entry.")
        given = author.get("given")
        family = author.get("family")
        name = author.get("name")
        parts: list[str] = []
        for value in (given, family):
            if value is None:
                continue
            parts.append(_bounded_text(value, field="author name", max_length=_MAX_AUTHOR_NAME_LENGTH))
        if parts:
            display = " ".join(parts)
        elif name is not None:
            display = _bounded_text(name, field="author name", max_length=_MAX_AUTHOR_NAME_LENGTH)
        else:
            continue
        if len(display) > _MAX_AUTHOR_NAME_LENGTH:
            raise ProviderResultValidationError("Crossref work has an overlong author name.")
        names.append(display)
    return tuple(names)


def _work_from_payload(payload: dict[str, object], *, expected_doi: str) -> dict[str, object]:
    if payload.get("status") != "ok" or payload.get("message-type") != "work":
        raise ProviderResultValidationError("Crossref REST API returned an invalid singleton envelope.")
    message = payload.get("message")
    if not isinstance(message, dict):
        raise ProviderResultValidationError("Crossref REST API response is missing the work record.")

    returned_doi = message.get("DOI")
    if not isinstance(returned_doi, str):
        raise ProviderResultValidationError("Crossref work is missing its DOI.")
    canonical_doi = validated_doi(returned_doi.strip())
    if canonical_doi is None or canonical_doi.casefold() != expected_doi.casefold():
        raise ProviderResultValidationError("Crossref returned a different DOI.")

    details: dict[str, object] = {
        "crossref_doi": canonical_doi,
        "crossref_title": _title_from_message(message),
        "crossref_author_names": list(_author_names(message)),
        "author_names_display_only": True,
        "api_attribution": "Crossref",
        "identity_claim": False,
    }
    year = _publication_year(message)
    if year is not None:
        details["crossref_publication_year"] = year
    return details


class CrossrefExactWorkProvider:
    descriptor = PROVIDER_BY_NAME["crossref_exact_work"]

    def __init__(self, *, fetcher: CrossrefFetch = fetch_crossref_work) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Crossref exact-work lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("Crossref exact-work lookup only accepts URLs.")

        doi = crossref_doi_from_url(query.identifier_value)
        if doi is None:
            raise ProviderValidationError("Crossref exact-work lookup requires an exact DOI URL.")

        payload = await self.fetcher(doi)
        if payload is None:
            return ProviderResult(observations=())
        details = _work_from_payload(payload, expected_doi=doi)
        canonical_doi = str(details["crossref_doi"])
        source_locator = f"https://doi.org/{quote(canonical_doi, safe='/')}"
        return ProviderResult(
            observations=(
                ProviderObservationData(source_locator=source_locator, payload=details),
            )
        )
