# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers import zenodo_record as zenodo
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers.zenodo_record import ZenodoExactRecordProvider, zenodo_record_id_from_url


RECORD_ID = "8435696"
RECORD_URL = f"https://zenodo.org/records/{RECORD_ID}"


def _query(kind: str = "url", value: str = RECORD_URL) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _payload(*, record_id: object = RECORD_ID) -> dict[str, object]:
    return {
        "id": record_id,
        "metadata": {
            "title": "Example preserved research object",
            "description": "not retained",
            "creators": [{"name": "Not Retained", "orcid": "0000-0000-0000-0000"}],
            "communities": [{"identifier": "not-retained"}],
            "related_identifiers": [{"identifier": "10.0000/not-retained"}],
        },
        "files": [{"key": "not-retained.zip", "checksum": "not-retained"}],
        "links": {"latest": "https://zenodo.org/api/records/not-followed"},
    }


def test_zenodo_url_admission_is_exact_and_canonical() -> None:
    assert zenodo_record_id_from_url(RECORD_URL) == RECORD_ID

    for value in (
        f"http://zenodo.org/records/{RECORD_ID}",
        f"https://www.zenodo.org/records/{RECORD_ID}",
        f"https://zenodo.org/records/{RECORD_ID}/",
        f"https://zenodo.org/records/{RECORD_ID}?x=1",
        f"https://zenodo.org/records/{RECORD_ID}#x",
        f"https://zenodo.org:443/records/{RECORD_ID}",
        f"https://user:secret@zenodo.org/records/{RECORD_ID}",
        f"https://zenodo.org/record/{RECORD_ID}",
        "https://zenodo.org/records/0",
        "https://zenodo.org/records/abc",
    ):
        assert zenodo_record_id_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_bounded_cc0_metadata_and_emits_no_leads() -> None:
    async def fetcher(record_id: str) -> dict[str, object]:
        assert record_id == RECORD_ID
        return _payload()

    result = await ZenodoExactRecordProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == RECORD_URL
    assert observation.payload == {
        "zenodo_record_id": RECORD_ID,
        "zenodo_record_title": "Example preserved research object",
        "data_license": "CC0",
        "api_attribution": "Zenodo (CERN)",
        "identity_claim": False,
    }
    for excluded in (
        "description",
        "creators",
        "communities",
        "related_identifiers",
        "files",
        "links",
    ):
        assert excluded not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="zenodo_exact_record",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_mismatch_and_invalid_input_fail_closed() -> None:
    async def missing(record_id: str):
        return None

    provider = ZenodoExactRecordProvider(fetcher=missing)
    assert (await provider.execute(_query(), None)).observations == ()

    async def mismatch(record_id: str) -> dict[str, object]:
        return _payload(record_id="1234")

    with pytest.raises(ProviderResultValidationError, match="different record id"):
        await ZenodoExactRecordProvider(fetcher=mismatch).execute(_query(), None)

    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="username", value=RECORD_ID), None)
    with pytest.raises(ProviderValidationError, match="canonical record URL"):
        await provider.execute(_query(value=f"{RECORD_URL}/"), None)


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
        return _Response(json.dumps(_payload()).encode())

    monkeypatch.setattr(zenodo, "urlopen", fake_urlopen)
    assert zenodo._fetch_zenodo_record_sync(RECORD_ID) == _payload()
    assert seen["url"] == f"https://zenodo.org/api/records/{RECORD_ID}"
    assert "github.com/tushar-rawat-22/persona-lattice" in seen["user_agent"]


def test_transport_maps_404_429_transient_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = Message()
    headers["Retry-After"] = "7"

    def not_found(request, timeout: float):
        raise HTTPError(request.full_url, 404, "missing", Message(), None)

    monkeypatch.setattr(zenodo, "urlopen", not_found)
    assert zenodo._fetch_zenodo_record_sync(RECORD_ID) is None

    def limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "limited", headers, None)

    monkeypatch.setattr(zenodo, "urlopen", limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        zenodo._fetch_zenodo_record_sync(RECORD_ID)
    assert exc_info.value.retry_after == 7.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "down", Message(), None)

    monkeypatch.setattr(zenodo, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        zenodo._fetch_zenodo_record_sync(RECORD_ID)

    monkeypatch.setattr(
        zenodo,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (zenodo._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge):
        zenodo._fetch_zenodo_record_sync(RECORD_ID)
