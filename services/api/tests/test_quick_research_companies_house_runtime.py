# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderResultValidationError, ProviderRemoteRateLimitError
from app.providers.shared_runtime import DEFAULT_COMPANIES_HOUSE_PROVIDER, DEFAULT_PROVIDER_RUNTIME
from app.research import ResearchKind, run_quick_research


COMPANY_NUMBER = "00000006"
COMPANY_URL = (
    "https://find-and-update.company-information.service.gov.uk/company/"
    f"{COMPANY_NUMBER}"
)


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


def _payload() -> dict[str, object]:
    return {
        "company_number": COMPANY_NUMBER,
        "company_name": "EXAMPLE COMPANY LIMITED",
        "company_status": "active",
        "type": "ltd",
        "date_of_creation": "1900-01-01",
        "registered_office_address": {"address_line_1": "Not retained"},
    }


@pytest.mark.asyncio
async def test_exact_company_url_executes_shared_runtime(monkeypatch) -> None:
    async def fetcher(company_number: str, secret: str) -> dict[str, object]:
        assert company_number == COMPANY_NUMBER
        assert secret == "free-companies-house-key"
        return _payload()

    monkeypatch.setattr(DEFAULT_PROVIDER_RUNTIME, "secret_resolver", lambda name: "free-companies-house-key")
    monkeypatch.setattr(DEFAULT_COMPANIES_HOUSE_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=COMPANY_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(
        item for item in report.observations if item.source == "companies_house_exact_company"
    )
    assert observation.source_locator == COMPANY_URL
    assert observation.details == {
        "companies_house_company_number": COMPANY_NUMBER,
        "companies_house_registered_name": "EXAMPLE COMPANY LIMITED",
        "companies_house_status": "active",
        "companies_house_type": "ltd",
        "api_attribution": "Companies House public register",
        "identity_claim": False,
        "companies_house_incorporation_date": "1900-01-01",
    }
    source_run = next(
        item for item in report.source_runs if item.source_name == "companies_house_exact_company"
    )
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_companies_house_provider(monkeypatch) -> None:
    async def should_not_run(company_number: str, secret: str):
        raise AssertionError("Companies House provider must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_COMPANIES_HOUSE_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )
    assert all(item.source != "companies_house_exact_company" for item in report.observations)
    assert all(item.source_name != "companies_house_exact_company" for item in report.source_runs)


@pytest.mark.asyncio
async def test_missing_companies_house_key_is_non_attempt_credential_state(monkeypatch) -> None:
    monkeypatch.setattr(DEFAULT_PROVIDER_RUNTIME, "secret_resolver", lambda name: None)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=COMPANY_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(
        item for item in report.source_runs if item.source_name == "companies_house_exact_company"
    )
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is SourceRunReason.CREDENTIAL_NOT_CONFIGURED
    assert source_run.execution_attempted is False
    assert "Companies House exact-company metadata was temporarily unavailable." not in report.warnings


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "expected_reason"),
    [
        (ProviderRemoteRateLimitError("remote limit", retry_after=3.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad returned company"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_companies_house_runtime_preserves_attempted_failure_phase(
    monkeypatch,
    exc,
    expected_reason,
) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._companies_house_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=COMPANY_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(
        item for item in report.source_runs if item.source_name == "companies_house_exact_company"
    )
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is expected_reason
    assert source_run.execution_attempted is True
    assert "Companies House exact-company metadata was temporarily unavailable." in report.warnings
