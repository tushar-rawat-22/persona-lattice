# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunState
from app.models import Purpose
from app.providers.shared_runtime import DEFAULT_SEC_EDGAR_PROVIDER
from app.research import ResearchKind, run_quick_research


CIK = "0000320193"
SEC_URL = "https://data.sec.gov/submissions/CIK0000320193.json"


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


def _payload() -> dict[str, object]:
    return {
        "cik": 320193,
        "name": "Apple Inc.",
        "sic": "3571",
        "stateOfIncorporation": "CA",
        "fiscalYearEnd": "0927",
        "tickers": ["AAPL"],
        "exchanges": ["Nasdaq"],
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-26-000100"],
                "filingDate": ["2026-08-01"],
                "form": ["10-Q"],
            }
        },
    }


@pytest.mark.asyncio
async def test_exact_sec_submissions_url_executes_shared_runtime(monkeypatch) -> None:
    async def fetcher(cik: str, *, user_agent: str) -> dict[str, object]:
        assert cik == CIK
        assert user_agent == "PersonaLattice ops@example.com"
        return _payload()

    monkeypatch.setattr(DEFAULT_SEC_EDGAR_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr(
        DEFAULT_SEC_EDGAR_PROVIDER,
        "user_agent_loader",
        lambda: "PersonaLattice ops@example.com",
    )
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=SEC_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(item for item in report.observations if item.source == "sec_edgar_exact_cik")
    assert observation.source_locator == SEC_URL
    assert observation.details["sec_cik"] == CIK
    assert observation.details["sec_filer_name"] == "Apple Inc."
    assert observation.details["identity_claim"] is False

    source_run = next(item for item in report.source_runs if item.source_name == "sec_edgar_exact_cik")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_sec_provider(monkeypatch) -> None:
    async def should_not_run(*args, **kwargs):
        raise AssertionError("SEC EDGAR provider must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_SEC_EDGAR_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr(
        DEFAULT_SEC_EDGAR_PROVIDER,
        "user_agent_loader",
        lambda: "PersonaLattice ops@example.com",
    )
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    assert all(item.source != "sec_edgar_exact_cik" for item in report.observations)
    assert all(item.source_name != "sec_edgar_exact_cik" for item in report.source_runs)
