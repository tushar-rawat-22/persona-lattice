# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers import ror_organization as ror
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers.ror_organization import RorExactOrganizationProvider, ror_id_from_url


ROR_ID = "015w2mp89"
ROR_URL = f"https://ror.org/{ROR_ID}"


def _query(kind: str = "url", value: str = ROR_URL) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _payload(*, status: str = "active", returned_id: str = ROR_URL) -> dict[str, object]:
    return {
        "id": returned_id,
        "status": status,
        "names": [
            {
                "lang": "en",
                "types": ["ror_display", "label"],
                "value": "Example Research Institute",
            },
            {
                "lang": "en",
                "types": ["alias"],
                "value": "Not retained alias",
            },
        ],
        "types": ["education", "funder"],
        "external_ids": [{"type": "fundref", "all": ["not-retained"]}],
        "domains": ["example.edu"],
        "links": [{"type": "website", "value": "https://example.edu"}],
        "locations": [{"geonames_details": {"name": "Not retained"}}],
        "relationships": [{"type": "related", "id": "https://ror.org/012345678"}],
    }


def test_ror_url_admission_is_exact_and_canonical() -> None:
    assert ror_id_from_url(ROR_URL) == ROR_ID

    for value in (
        f"http://ror.org/{ROR_ID}",
        f"https://www.ror.org/{ROR_ID}",
        f"https://ror.org/{ROR_ID}/",
        f"https://ror.org/{ROR_ID}?x=1",
        f"https://ror.org/{ROR_ID}#x",
        f"https://ror.org:443/{ROR_ID}",
        f"https://user:secret@ror.org/{ROR_ID}",
        f"https://ror.org/orgs/{ROR_ID}",
        "https://ror.org/015w2mp8",
        "https://ror.org/115w2mp89",
        "https://ror.org/015i2mp89",
    ):
        assert ror_id_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_bounded_registry_metadata_and_emits_no_leads() -> None:
    async def fetcher(ror_id: str) -> dict[str, object]:
        assert ror_id == ROR_ID
        return _payload()

    result = await RorExactOrganizationProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == ROR_URL
    assert observation.payload == {
        "ror_id": ROR_URL,
        "ror_display_name": "Example Research Institute",
        "record_status": "active",
        "data_license": "CC0",
        "api_attribution": "Research Organization Registry (ROR)",
        "identity_claim": False,
        "organization_types": ["education", "funder"],
    }
    for excluded in ("external_ids", "domains", "links", "locations", "relationships"):
        assert excluded not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="ror_exact_organization",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_record_is_completed_zero_observation_result() -> None:
    async def fetcher(ror_id: str):
        return None

    result = await RorExactOrganizationProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_secret_wrong_kind_and_noncanonical_url() -> None:
    provider = RorExactOrganizationProvider(fetcher=lambda ror_id: None)  # type: ignore[arg-type]
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="organization", value=ROR_ID), None)
    with pytest.raises(ProviderValidationError, match="requires a canonical ROR URL"):
        await provider.execute(_query(value=f"https://ror.org/{ROR_ID}/"), None)


@pytest.mark.asyncio
async def test_mismatch_non_active_and_ambiguous_display_name_fail_closed() -> None:
    async def mismatch(ror_id: str) -> dict[str, object]:
        return _payload(returned_id="https://ror.org/03yrm5c26")

    with pytest.raises(ProviderResultValidationError, match="different organization id"):
        await RorExactOrganizationProvider(fetcher=mismatch).execute(_query(), None)

    async def inactive(ror_id: str) -> dict[str, object]:
        return _payload(status="inactive")

    with pytest.raises(ProviderResultValidationError, match="non-active"):
        await RorExactOrganizationProvider(fetcher=inactive).execute(_query(), None)

    ambiguous_payload = _payload()
    names = ambiguous_payload["names"]
    assert isinstance(names, list)
    names.append({"types": ["ror_display"], "value": "Another display name"})

    async def ambiguous(ror_id: str) -> dict[str, object]:
        return ambiguous_payload

    with pytest.raises(ProviderResultValidationError, match="exactly one display name"):
        await RorExactOrganizationProvider(fetcher=ambiguous).execute(_query(), None)


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

    monkeypatch.setattr(ror, "urlopen", fake_urlopen)
    assert ror._fetch_ror_organization_sync(ROR_ID) == _payload()
    assert seen["url"] == f"https://api.ror.org/v2/organizations/{ROR_ID}"
    assert "github.com/tushar-rawat-22/persona-lattice" in seen["user_agent"]


def test_transport_maps_404_429_transient_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = Message()
    headers["Retry-After"] = "11"

    def not_found(request, timeout: float):
        raise HTTPError(request.full_url, 404, "missing", Message(), None)

    monkeypatch.setattr(ror, "urlopen", not_found)
    assert ror._fetch_ror_organization_sync(ROR_ID) is None

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "limited", headers, None)

    monkeypatch.setattr(ror, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        ror._fetch_ror_organization_sync(ROR_ID)
    assert exc_info.value.retry_after == 11.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "down", Message(), None)

    monkeypatch.setattr(ror, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        ror._fetch_ror_organization_sync(ROR_ID)

    monkeypatch.setattr(
        ror,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (ror._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge):
        ror._fetch_ror_organization_sync(ROR_ID)
