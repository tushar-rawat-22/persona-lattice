# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers import datacite_doi as datacite
from app.providers.datacite_doi import DataCiteExactDoiProvider


def _query(
    kind: str = "url",
    value: str = "https://doi.org/10.5438/0012",
) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _payload(doi: str = "10.5438/0012") -> dict[str, object]:
    return {
        "data": {
            "id": doi,
            "type": "dois",
            "attributes": {
                "doi": doi,
                "state": "findable",
                "titles": [{"title": "A bounded DataCite title"}],
                "publicationYear": 2024,
                "types": {"resourceTypeGeneral": "Dataset", "resourceType": "Research data"},
                "creators": [
                    {
                        "name": "Example, Ada",
                        "nameIdentifiers": [{"nameIdentifier": "https://orcid.org/0000-0000-0000-0000"}],
                        "affiliation": [{"name": "not retained"}],
                    },
                    {"givenName": "Grace", "familyName": "Example"},
                ],
                "contributors": [{"name": "not retained"}],
                "descriptions": [{"description": "not retained"}],
                "geoLocations": [{"geoLocationPlace": "not retained"}],
                "fundingReferences": [{"funderName": "not retained"}],
                "relatedIdentifiers": [{"relatedIdentifier": "10.9999/not-retained"}],
                "subjects": [{"subject": "not retained"}],
                "rightsList": [{"rightsUri": "https://example.invalid/not-retained"}],
                "url": "https://example.invalid/not-retained",
                "views": 123,
                "downloads": 456,
            },
        }
    }


@pytest.mark.asyncio
async def test_success_retains_bounded_cc0_metadata_and_emits_no_leads() -> None:
    async def fetcher(doi: str) -> dict[str, object]:
        assert doi == "10.5438/0012"
        return _payload()

    result = await DataCiteExactDoiProvider(fetcher=fetcher).execute(_query(), None)
    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://doi.org/10.5438/0012"
    assert observation.payload == {
        "datacite_doi": "10.5438/0012",
        "datacite_title": "A bounded DataCite title",
        "datacite_creator_names": ["Example, Ada", "Grace Example"],
        "creator_names_display_only": True,
        "data_license": "CC0",
        "api_attribution": "DataCite",
        "identity_claim": False,
        "datacite_publication_year": 2024,
        "datacite_resource_type": "Dataset",
    }
    forbidden = {
        "nameIdentifiers",
        "affiliation",
        "contributors",
        "descriptions",
        "geoLocations",
        "fundingReferences",
        "relatedIdentifiers",
        "subjects",
        "rightsList",
        "url",
        "views",
        "downloads",
    }
    assert forbidden.isdisjoint(observation.payload)
    extraction = extract_observation_leads(
        details=observation.payload,
        source="datacite_exact_doi",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_doi_is_completed_zero_observation_result() -> None:
    async def fetcher(doi: str) -> None:
        return None

    result = await DataCiteExactDoiProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_secret_wrong_kind_and_non_doi_url() -> None:
    async def fetcher(doi: str):
        return None

    provider = DataCiteExactDoiProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="username", value="10.5438/0012"), None)
    with pytest.raises(ProviderValidationError, match="requires an exact DOI URL"):
        await provider.execute(_query(value="https://example.com/10.5438/0012"), None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "invalid singleton envelope"),
        ({"data": {"id": "10.5438/0012", "type": "dois", "attributes": {}}}, "missing a title"),
        ({"data": {"id": "10.9999/other", "type": "dois", "attributes": {"titles": [{"title": "X"}]} }}, "different DOI"),
        ({"data": {"id": "10.5438/0012", "type": "dois", "attributes": {"doi": "10.5438/0012", "state": "registered", "titles": [{"title": "X"}]} }}, "non-Findable"),
    ],
)
async def test_malformed_or_non_findable_results_fail_closed(payload: dict[str, object], message: str) -> None:
    async def fetcher(doi: str) -> dict[str, object]:
        return payload

    with pytest.raises(ProviderResultValidationError, match=message):
        await DataCiteExactDoiProvider(fetcher=fetcher).execute(_query(), None)


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw
        self.headers = Message()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def test_transport_uses_singleton_endpoint_and_identifying_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 4.0
        return _Response(json.dumps(_payload("10.5438/ABC(12)"), separators=(",", ":")).encode())

    monkeypatch.setattr(datacite, "urlopen", fake_urlopen)
    payload = datacite._fetch_datacite_doi_sync("10.5438/ABC(12)")
    assert payload == _payload("10.5438/ABC(12)")
    assert seen["url"] == "https://api.datacite.org/dois/10.5438%2FABC%2812%29"
    assert seen["user_agent"] == "PersonaLattice/0.0.1 datacite-exact-doi-fallback"


def test_transport_maps_404_429_transient_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(request, timeout: float):
        raise HTTPError(request.full_url, 404, "missing", Message(), None)

    monkeypatch.setattr(datacite, "urlopen", missing)
    assert datacite._fetch_datacite_doi_sync("10.5438/0012") is None

    headers = Message()
    headers["Retry-After"] = "9"

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "rate limited", headers, None)

    monkeypatch.setattr(datacite, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        datacite._fetch_datacite_doi_sync("10.5438/0012")
    assert exc_info.value.retry_after == 9.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "unavailable", Message(), None)

    monkeypatch.setattr(datacite, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        datacite._fetch_datacite_doi_sync("10.5438/0012")

    monkeypatch.setattr(
        datacite,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (datacite._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge, match="exceeded the adapter limit"):
        datacite._fetch_datacite_doi_sync("10.5438/0012")
