# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .crossref_work import crossref_doi_from_url
from .errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from .registry import PROVIDER_BY_NAME


_API_ROOT = "https://api.datacite.org/dois"
_USER_AGENT = "PersonaLattice/0.0.1 datacite-exact-doi-fallback"
_MAX_RAW_RESPONSE_BYTES = 32 * 1024
_MAX_TITLE_LENGTH = 300
_MAX_CREATOR_COUNT = 8
_MAX_CREATOR_NAME_LENGTH = 120
_MAX_RESOURCE_TYPE_LENGTH = 80

DataCiteFetch = Callable[[str], Awaitable[dict[str, object] | None]]


def _retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _fetch_datacite_doi_sync(doi: str) -> dict[str, object] | None:
    request_url = f"{_API_ROOT}/{quote(doi, safe='')}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/vnd.api+json",
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
            raise ProviderTransientError("DataCite REST API was unavailable.") from exc
        raise ProviderExecutionError("DataCite REST API rejected the request.") from exc
    except (URLError, TimeoutError) as exc:
        raise ProviderTransientError("DataCite REST API was unavailable.") from exc

    if len(raw) > _MAX_RAW_RESPONSE_BYTES:
        raise ProviderResponseTooLarge("DataCite REST API response exceeded the adapter limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderResultValidationError("DataCite REST API returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ProviderResultValidationError("DataCite REST API returned an invalid response shape.")
    return payload


async def fetch_datacite_doi(doi: str) -> dict[str, object] | None:
    return await asyncio.to_thread(_fetch_datacite_doi_sync, doi)


def _bounded_text(value: object, *, field: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ProviderResultValidationError(f"DataCite DOI has an invalid {field}.")
    text = " ".join(value.split())
    if not text or len(text) > max_length:
        raise ProviderResultValidationError(f"DataCite DOI has an invalid {field}.")
    return text


def _title(attributes: dict[str, object]) -> str:
    titles = attributes.get("titles")
    if not isinstance(titles, list) or not titles or not isinstance(titles[0], dict):
        raise ProviderResultValidationError("DataCite DOI is missing a title.")
    return _bounded_text(titles[0].get("title"), field="title", max_length=_MAX_TITLE_LENGTH)


def _publication_year(attributes: dict[str, object]) -> int | None:
    value = attributes.get("publicationYear")
    if value is None:
        return None
    if isinstance(value, bool):
        raise ProviderResultValidationError("DataCite DOI has an invalid publication year.")
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if not isinstance(value, int) or value < 1000 or value > 9999:
        raise ProviderResultValidationError("DataCite DOI has an invalid publication year.")
    return value


def _creator_names(attributes: dict[str, object]) -> tuple[str, ...]:
    creators = attributes.get("creators")
    if creators is None:
        return ()
    if not isinstance(creators, list):
        raise ProviderResultValidationError("DataCite DOI has an invalid creator list.")

    names: list[str] = []
    for creator in creators[:_MAX_CREATOR_COUNT]:
        if not isinstance(creator, dict):
            raise ProviderResultValidationError("DataCite DOI has an invalid creator entry.")
        name = creator.get("name")
        if name is not None:
            names.append(_bounded_text(name, field="creator name", max_length=_MAX_CREATOR_NAME_LENGTH))
            continue
        given = creator.get("givenName")
        family = creator.get("familyName")
        parts: list[str] = []
        for value in (given, family):
            if value is not None:
                parts.append(
                    _bounded_text(value, field="creator name", max_length=_MAX_CREATOR_NAME_LENGTH)
                )
        if parts:
            display = " ".join(parts)
            if len(display) > _MAX_CREATOR_NAME_LENGTH:
                raise ProviderResultValidationError("DataCite DOI has an overlong creator name.")
            names.append(display)
    return tuple(names)


def _resource_type(attributes: dict[str, object]) -> str | None:
    resource_types = attributes.get("types")
    if resource_types is None:
        return None
    if not isinstance(resource_types, dict):
        raise ProviderResultValidationError("DataCite DOI has an invalid resource type.")
    value = resource_types.get("resourceTypeGeneral")
    if value is None:
        return None
    return _bounded_text(value, field="resource type", max_length=_MAX_RESOURCE_TYPE_LENGTH)


def _details_from_payload(payload: dict[str, object], *, expected_doi: str) -> dict[str, object]:
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("type") != "dois":
        raise ProviderResultValidationError("DataCite REST API returned an invalid singleton envelope.")
    attributes = data.get("attributes")
    if not isinstance(attributes, dict):
        raise ProviderResultValidationError("DataCite REST API response is missing DOI attributes.")

    returned_doi = attributes.get("doi")
    if not isinstance(returned_doi, str):
        returned_doi = data.get("id")
    if not isinstance(returned_doi, str) or returned_doi.strip().casefold() != expected_doi.casefold():
        raise ProviderResultValidationError("DataCite returned a different DOI.")

    state = attributes.get("state")
    if state is not None and state != "findable":
        raise ProviderResultValidationError("DataCite returned a non-Findable DOI record.")

    canonical_doi = returned_doi.strip()
    details: dict[str, object] = {
        "datacite_doi": canonical_doi,
        "datacite_title": _title(attributes),
        "datacite_creator_names": list(_creator_names(attributes)),
        "creator_names_display_only": True,
        "data_license": "CC0",
        "api_attribution": "DataCite",
        "identity_claim": False,
    }
    year = _publication_year(attributes)
    if year is not None:
        details["datacite_publication_year"] = year
    resource_type = _resource_type(attributes)
    if resource_type is not None:
        details["datacite_resource_type"] = resource_type
    return details


class DataCiteExactDoiProvider:
    descriptor = PROVIDER_BY_NAME["datacite_exact_doi"]

    def __init__(self, *, fetcher: DataCiteFetch = fetch_datacite_doi) -> None:
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("DataCite exact-DOI lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("DataCite exact-DOI lookup only accepts URLs.")

        doi = crossref_doi_from_url(query.identifier_value)
        if doi is None:
            raise ProviderValidationError("DataCite exact-DOI lookup requires an exact DOI URL.")

        payload = await self.fetcher(doi)
        if payload is None:
            return ProviderResult(observations=())
        details = _details_from_payload(payload, expected_doi=doi)
        canonical_doi = str(details["datacite_doi"])
        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"https://doi.org/{quote(canonical_doi, safe='/')}",
                    payload=details,
                ),
            )
        )
