# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers import wikidata_entity as wikidata
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers.wikidata_entity import WikidataExactEntityProvider, wikidata_entity_id_from_url


def _query(
    kind: str = "url",
    value: str = "https://www.wikidata.org/wiki/Q42",
) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _payload(entity_id: str = "Q42") -> dict[str, object]:
    return {
        "entities": {
            entity_id: {
                "id": entity_id,
                "type": "item",
                "labels": {"en": {"language": "en", "value": "Douglas Adams"}},
                "descriptions": {
                    "en": {
                        "language": "en",
                        "value": "English writer and humorist",
                    }
                },
                "claims": {"P569": [{"not": "retained"}]},
                "sitelinks": {"enwiki": {"title": "not retained"}},
            }
        }
    }


def test_entity_url_admission_is_exact() -> None:
    assert wikidata_entity_id_from_url("https://www.wikidata.org/wiki/Q42") == "Q42"
    assert wikidata_entity_id_from_url("https://www.wikidata.org/wiki/Q42/") == "Q42"

    for value in (
        "http://www.wikidata.org/wiki/Q42",
        "https://wikidata.org/wiki/Q42",
        "https://www.wikidata.org/wiki/P31",
        "https://www.wikidata.org/wiki/Q0",
        "https://www.wikidata.org/wiki/Q42?x=1",
        "https://www.wikidata.org/wiki/Q42#x",
        "https://www.wikidata.org:443/wiki/Q42",
        "https://user:secret@www.wikidata.org/wiki/Q42",
        "https://www.wikidata.org/w/index.php?title=Q42",
    ):
        assert wikidata_entity_id_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_bounded_cc0_metadata_and_emits_no_leads() -> None:
    async def fetcher(entity_id: str) -> dict[str, object]:
        assert entity_id == "Q42"
        return _payload()

    result = await WikidataExactEntityProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://www.wikidata.org/wiki/Q42"
    assert observation.payload == {
        "wikidata_entity_id": "Q42",
        "data_license": "CC0",
        "api_attribution": "Wikidata",
        "identity_claim": False,
        "wikidata_label_en": "Douglas Adams",
        "wikidata_description_en": "English writer and humorist",
    }
    assert "claims" not in observation.payload
    assert "sitelinks" not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="wikidata_exact_entity",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_entity_is_completed_zero_observation_result() -> None:
    async def fetcher(entity_id: str) -> dict[str, object]:
        return {
            "entities": {
                entity_id: {
                    "id": entity_id,
                    "type": "item",
                    "missing": "",
                }
            }
        }

    result = await WikidataExactEntityProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_secret_wrong_kind_and_non_entity_url() -> None:
    provider = WikidataExactEntityProvider(
        fetcher=lambda entity_id: None  # type: ignore[arg-type]
    )
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="username", value="Q42"), None)
    with pytest.raises(ProviderValidationError, match="requires an exact item URL"):
        await provider.execute(_query(value="https://www.wikidata.org/wiki/P31"), None)


@pytest.mark.asyncio
async def test_mismatched_entity_fails_closed() -> None:
    async def mismatch(entity_id: str) -> dict[str, object]:
        return {
            "entities": {
                entity_id: {
                    "id": "Q99",
                    "type": "item",
                    "labels": {"en": {"value": "X"}},
                }
            }
        }

    with pytest.raises(ProviderResultValidationError, match="different entity id"):
        await WikidataExactEntityProvider(fetcher=mismatch).execute(_query(), None)


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def test_transport_is_exact_bounded_identified_and_requests_maxlag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 4.0
        return _Response(json.dumps(_payload()).encode())

    monkeypatch.setattr(wikidata, "urlopen", fake_urlopen)
    assert wikidata._fetch_wikidata_entity_sync("Q42") == _payload()
    assert "action=wbgetentities" in seen["url"]
    assert "ids=Q42" in seen["url"]
    assert "props=labels%7Cdescriptions" in seen["url"]
    assert "languages=en" in seen["url"]
    assert "maxlag=5" in seen["url"]
    assert "github.com%2Ftushar" not in seen["url"]
    assert "github.com/tushar-rawat-22/persona-lattice" in seen["user_agent"]


def test_transport_maps_http_429_transient_and_oversized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = Message()
    headers["Retry-After"] = "7"

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "limited", headers, None)

    monkeypatch.setattr(wikidata, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        wikidata._fetch_wikidata_entity_sync("Q42")
    assert exc_info.value.retry_after == 7.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "down", Message(), None)

    monkeypatch.setattr(wikidata, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        wikidata._fetch_wikidata_entity_sync("Q42")

    monkeypatch.setattr(
        wikidata,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (wikidata._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge):
        wikidata._fetch_wikidata_entity_sync("Q42")


def test_transport_maps_action_api_rate_limit_and_maxlag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        wikidata,
        "urlopen",
        lambda request, timeout: _Response(
            json.dumps({"error": {"code": "ratelimited", "info": "slow down"}}).encode()
        ),
    )
    with pytest.raises(ProviderRemoteRateLimitError):
        wikidata._fetch_wikidata_entity_sync("Q42")

    monkeypatch.setattr(
        wikidata,
        "urlopen",
        lambda request, timeout: _Response(
            json.dumps({"error": {"code": "maxlag", "info": "waiting for replicas"}}).encode()
        ),
    )
    with pytest.raises(ProviderTransientError, match="replication lag"):
        wikidata._fetch_wikidata_entity_sync("Q42")
