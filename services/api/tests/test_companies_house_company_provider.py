# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import base64
from email.message import Message
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers import companies_house_company as companies_house
from app.providers.base import ProviderQuery
from app.providers.companies_house_company import (
    CompaniesHouseExactCompanyProvider,
    companies_house_number_from_url,
)
from app.providers.errors import (
    ProviderExecutionError,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)


COMPANY_NUMBER = "00000006"
COMPANY_URL = (
    "https://find-and-update.company-information.service.gov.uk/company/"
    f"{COMPANY_NUMBER}"
)


def _query(kind: str = "url", value: str = COMPANY_URL) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _payload(*, returned_number: str = COMPANY_NUMBER) -> dict[str, object]:
    return {
        "company_number": returned_number,
        "company_name": "EXAMPLE COMPANY LIMITED",
        "company_status": "active",
        "type": "ltd",
        "date_of_creation": "1900-01-01",
        "registered_office_address": {"address_line_1": "Not retained"},
        "sic_codes": ["62020"],
        "accounts": {"next_due": "2099-01-01"},
        "confirmation_statement": {"next_due": "2099-01-01"},
        "previous_company_names": [{"name": "Not retained"}],
        "links": {"officers": "/company/00000006/officers"},
        "jurisdiction": "england-wales",
        "has_insolvency_history": True,
        "has_charges": True,
    }


def test_company_url_admission_is_exact_and_canonical() -> None:
    assert companies_house_number_from_url(COMPANY_URL) == COMPANY_NUMBER
    assert (
        companies_house_number_from_url(
            "https://find-and-update.company-information.service.gov.uk/company/SC123456"
        )
        == "SC123456"
    )

    for value in (
        f"http://find-and-update.company-information.service.gov.uk/company/{COMPANY_NUMBER}",
        f"https://www.company-information.service.gov.uk/company/{COMPANY_NUMBER}",
        f"https://find-and-update.company-information.service.gov.uk/company/{COMPANY_NUMBER}/",
        f"https://find-and-update.company-information.service.gov.uk/company/{COMPANY_NUMBER}?x=1",
        f"https://find-and-update.company-information.service.gov.uk/company/{COMPANY_NUMBER}#x",
        f"https://find-and-update.company-information.service.gov.uk:443/company/{COMPANY_NUMBER}",
        f"https://user:secret@find-and-update.company-information.service.gov.uk/company/{COMPANY_NUMBER}",
        "https://find-and-update.company-information.service.gov.uk/search/companies?q=example",
        "https://find-and-update.company-information.service.gov.uk/company/123",
        "https://find-and-update.company-information.service.gov.uk/company/123456789",
    ):
        assert companies_house_number_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_bounded_company_metadata_and_emits_no_leads() -> None:
    async def fetcher(company_number: str, secret: str) -> dict[str, object]:
        assert company_number == COMPANY_NUMBER
        assert secret == "server-key"
        return _payload()

    result = await CompaniesHouseExactCompanyProvider(fetcher=fetcher).execute(
        _query(), "server-key"
    )

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == COMPANY_URL
    assert observation.payload == {
        "companies_house_company_number": COMPANY_NUMBER,
        "companies_house_registered_name": "EXAMPLE COMPANY LIMITED",
        "companies_house_status": "active",
        "companies_house_type": "ltd",
        "api_attribution": "Companies House public register",
        "identity_claim": False,
        "companies_house_incorporation_date": "1900-01-01",
    }
    for excluded in (
        "registered_office_address",
        "sic_codes",
        "accounts",
        "confirmation_statement",
        "previous_company_names",
        "links",
        "jurisdiction",
        "has_insolvency_history",
        "has_charges",
    ):
        assert excluded not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="companies_house_exact_company",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_record_is_completed_zero_observation_result() -> None:
    async def fetcher(company_number: str, secret: str):
        return None

    result = await CompaniesHouseExactCompanyProvider(fetcher=fetcher).execute(
        _query(), "server-key"
    )
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_missing_secret_wrong_kind_and_noncanonical_url() -> None:
    async def unused(company_number: str, secret: str):
        return None

    provider = CompaniesHouseExactCompanyProvider(fetcher=unused)
    with pytest.raises(ProviderValidationError, match="requires a server-side API key"):
        await provider.execute(_query(), None)
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="organization", value=COMPANY_NUMBER), "server-key")
    with pytest.raises(ProviderValidationError, match="requires a canonical public company URL"):
        await provider.execute(_query(value=f"{COMPANY_URL}/"), "server-key")


@pytest.mark.asyncio
async def test_mismatch_bad_date_and_missing_required_fields_fail_closed() -> None:
    async def mismatch(company_number: str, secret: str) -> dict[str, object]:
        return _payload(returned_number="00000007")

    with pytest.raises(ProviderResultValidationError, match="different company number"):
        await CompaniesHouseExactCompanyProvider(fetcher=mismatch).execute(_query(), "server-key")

    bad_date = _payload()
    bad_date["date_of_creation"] = "01-01-1900"

    async def invalid_date(company_number: str, secret: str) -> dict[str, object]:
        return bad_date

    with pytest.raises(ProviderResultValidationError, match="invalid date_of_creation"):
        await CompaniesHouseExactCompanyProvider(fetcher=invalid_date).execute(
            _query(), "server-key"
        )

    missing_name = _payload()
    missing_name.pop("company_name")

    async def invalid_name(company_number: str, secret: str) -> dict[str, object]:
        return missing_name

    with pytest.raises(ProviderResultValidationError, match="invalid company_name"):
        await CompaniesHouseExactCompanyProvider(fetcher=invalid_name).execute(
            _query(), "server-key"
        )


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def test_transport_uses_basic_auth_exact_endpoint_and_bounded_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["authorization"] = request.get_header("Authorization")
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 4.0
        return _Response(json.dumps(_payload()).encode())

    monkeypatch.setattr(companies_house, "urlopen", fake_urlopen)
    assert companies_house._fetch_company_sync(COMPANY_NUMBER, "server-key") == _payload()
    assert seen["url"] == f"https://api.company-information.service.gov.uk/company/{COMPANY_NUMBER}"
    expected = base64.b64encode(b"server-key:").decode("ascii")
    assert seen["authorization"] == f"Basic {expected}"
    assert "server-key" not in seen["url"]
    assert "github.com/tushar-rawat-22/persona-lattice" in seen["user_agent"]


def test_transport_maps_404_auth_429_transient_and_oversized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def not_found(request, timeout: float):
        raise HTTPError(request.full_url, 404, "missing", Message(), None)

    monkeypatch.setattr(companies_house, "urlopen", not_found)
    assert companies_house._fetch_company_sync(COMPANY_NUMBER, "server-key") is None

    def unauthorized(request, timeout: float):
        raise HTTPError(request.full_url, 401, "unauthorized", Message(), None)

    monkeypatch.setattr(companies_house, "urlopen", unauthorized)
    with pytest.raises(ProviderExecutionError, match="configured API credential"):
        companies_house._fetch_company_sync(COMPANY_NUMBER, "server-key")

    headers = Message()
    headers["Retry-After"] = "11"

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "limited", headers, None)

    monkeypatch.setattr(companies_house, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        companies_house._fetch_company_sync(COMPANY_NUMBER, "server-key")
    assert exc_info.value.retry_after == 11.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "down", Message(), None)

    monkeypatch.setattr(companies_house, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        companies_house._fetch_company_sync(COMPANY_NUMBER, "server-key")

    monkeypatch.setattr(
        companies_house,
        "urlopen",
        lambda request, timeout: _Response(
            b"x" * (companies_house._MAX_RAW_RESPONSE_BYTES + 1)
        ),
    )
    with pytest.raises(ProviderResponseTooLarge):
        companies_house._fetch_company_sync(COMPANY_NUMBER, "server-key")
