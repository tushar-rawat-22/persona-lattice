# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers import gleif_lei as gleif
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers.gleif_lei import GleifExactLeiProvider, gleif_lei_from_url


LEI = "5493001KJTIIGC8Y1R12"
GLEIF_URL = f"https://search.gleif.org/#/record/{LEI}"


def _query(kind: str = "url", value: str = GLEIF_URL) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _record(*, record_id: str = LEI, attribute_lei: str = LEI) -> dict[str, object]:
    return {
        "type": "lei-records",
        "id": record_id,
        "attributes": {
            "lei": attribute_lei,
            "entity": {
                "legalName": {"name": "Bloomberg Finance L.P.", "language": "en"},
                "status": "ACTIVE",
                "jurisdiction": "US-DE",
                "legalAddress": {"addressLines": ["not retained"], "city": "New York"},
                "headquartersAddress": {"addressLines": ["not retained"]},
                "otherNames": [{"name": "not retained"}],
            },
            "registration": {
                "status": "ISSUED",
                "lastUpdateDate": "2026-08-01T10:20:30Z",
                "managingLou": "not-retained",
            },
            "bic": ["not-retained"],
            "mic": ["not-retained"],
            "ocid": ["not-retained"],
            "spglobal": ["not-retained"],
        },
        "relationships": {
            "direct-parent": {"links": {"related": "not-retained"}},
            "ultimate-parent": {"links": {"related": "not-retained"}},
        },
    }


def test_gleif_url_admission_requires_exact_canonical_record_and_valid_checksum() -> None:
    assert gleif_lei_from_url(GLEIF_URL) == LEI

    for value in (
        f"http://search.gleif.org/#/record/{LEI}",
        f"https://www.search.gleif.org/#/record/{LEI}",
        f"https://search.gleif.org:443/#/record/{LEI}",
        f"https://user:secret@search.gleif.org/#/record/{LEI}",
        f"https://search.gleif.org/?x=1#/record/{LEI}",
        f"https://search.gleif.org/record/{LEI}",
        f"https://search.gleif.org/#/record/{LEI}/",
        f"https://search.gleif.org/#/record/{LEI[:-1]}3",
        f"https://search.gleif.org/#/record/{LEI.lower()}",
    ):
        assert gleif_lei_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_bounded_legal_entity_metadata_and_emits_no_leads() -> None:
    async def fetcher(lei: str) -> dict[str, object]:
        assert lei == LEI
        return _record()

    result = await GleifExactLeiProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == GLEIF_URL
    assert observation.payload == {
        "gleif_lei": LEI,
        "gleif_legal_name": "Bloomberg Finance L.P.",
        "entity_status": "ACTIVE",
        "registration_status": "ISSUED",
        "data_license": "CC0",
        "api_attribution": "Global Legal Entity Identifier Foundation (GLEIF)",
        "identity_claim": False,
        "legal_jurisdiction": "US-DE",
        "last_update_date": "2026-08-01T10:20:30Z",
    }
    for excluded in (
        "legalAddress",
        "headquartersAddress",
        "otherNames",
        "bic",
        "mic",
        "ocid",
        "spglobal",
        "relationships",
    ):
        assert excluded not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="gleif_exact_lei",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_record_is_completed_zero_observation_result() -> None:
    async def fetcher(lei: str):
        return None

    result = await GleifExactLeiProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_secret_wrong_kind_and_noncanonical_url() -> None:
    async def fetcher(lei: str):
        return None

    provider = GleifExactLeiProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="organization", value=LEI), None)
    with pytest.raises(ProviderValidationError, match="requires a canonical GLEIF record URL"):
        await provider.execute(_query(value=f"https://search.gleif.org/#/record/{LEI[:-1]}3"), None)


@pytest.mark.asyncio
async def test_mismatched_ids_and_missing_required_metadata_fail_closed() -> None:
    async def wrong_record_id(lei: str) -> dict[str, object]:
        return _record(record_id="529900T8BM49AURSDO55")

    with pytest.raises(ProviderResultValidationError, match="different LEI record id"):
        await GleifExactLeiProvider(fetcher=wrong_record_id).execute(_query(), None)

    async def wrong_attribute_lei(lei: str) -> dict[str, object]:
        return _record(attribute_lei="529900T8BM49AURSDO55")

    with pytest.raises(ProviderResultValidationError, match="different LEI in record attributes"):
        await GleifExactLeiProvider(fetcher=wrong_attribute_lei).execute(_query(), None)

    broken = _record()
    attributes = broken["attributes"]
    assert isinstance(attributes, dict)
    entity = attributes["entity"]
    assert isinstance(entity, dict)
    entity["legalName"] = {"name": ""}

    async def missing_name(lei: str) -> dict[str, object]:
        return broken

    with pytest.raises(ProviderResultValidationError, match="invalid legal name"):
        await GleifExactLeiProvider(fetcher=missing_name).execute(_query(), None)


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def test_transport_is_exact_bounded_and_identified(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 4.0
        return _Response(json.dumps({"data": [_record()]}).encode())

    monkeypatch.setattr(gleif, "urlopen", fake_urlopen)
    assert gleif._fetch_gleif_lei_sync(LEI) == _record()
    parts = urlsplit(seen["url"])
    assert parts.scheme == "https"
    assert parts.netloc == "api.gleif.org"
    assert parts.path == "/api/v1/lei-records"
    assert parse_qs(parts.query) == {"page[size]": ["1"], "filter[lei]": [LEI]}
    assert "github.com/tushar-rawat-22/persona-lattice" in seen["user_agent"]


def test_transport_maps_429_transient_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = Message()
    headers["Retry-After"] = "7"

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "limited", headers, None)

    monkeypatch.setattr(gleif, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        gleif._fetch_gleif_lei_sync(LEI)
    assert exc_info.value.retry_after == 7.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "down", Message(), None)

    monkeypatch.setattr(gleif, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        gleif._fetch_gleif_lei_sync(LEI)

    monkeypatch.setattr(
        gleif,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (gleif._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge):
        gleif._fetch_gleif_lei_sync(LEI)
