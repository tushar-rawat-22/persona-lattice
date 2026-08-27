# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderRemoteRateLimitError, ProviderResultValidationError
from app.providers.shared_runtime import DEFAULT_GLEIF_PROVIDER
from app.research import ResearchKind, run_quick_research


LEI = "5493001KJTIIGC8Y1R12"
GLEIF_URL = f"https://search.gleif.org/#/record/{LEI}"


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


def _record() -> dict[str, object]:
    return {
        "type": "lei-records",
        "id": LEI,
        "attributes": {
            "lei": LEI,
            "entity": {
                "legalName": {"name": "Bloomberg Finance L.P."},
                "status": "ACTIVE",
                "jurisdiction": "US-DE",
            },
            "registration": {
                "status": "ISSUED",
                "lastUpdateDate": "2026-08-01T10:20:30Z",
            },
        },
    }


@pytest.mark.asyncio
async def test_exact_gleif_url_executes_shared_runtime(monkeypatch) -> None:
    async def fetcher(lei: str) -> dict[str, object]:
        assert lei == LEI
        return _record()

    monkeypatch.setattr(DEFAULT_GLEIF_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=GLEIF_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(item for item in report.observations if item.source == "gleif_exact_lei")
    assert observation.source_locator == GLEIF_URL
    assert observation.details["gleif_lei"] == LEI
    assert observation.details["gleif_legal_name"] == "Bloomberg Finance L.P."
    assert observation.details["data_license"] == "CC0"
    assert observation.details["identity_claim"] is False
    source_run = next(item for item in report.source_runs if item.source_name == "gleif_exact_lei")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_gleif_provider(monkeypatch) -> None:
    async def should_not_run(lei: str):
        raise AssertionError("GLEIF provider must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_GLEIF_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )
    assert all(item.source != "gleif_exact_lei" for item in report.observations)
    assert all(item.source_name != "gleif_exact_lei" for item in report.source_runs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "expected_reason"),
    [
        (ProviderRemoteRateLimitError("remote limit", retry_after=3.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad returned LEI"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_gleif_runtime_preserves_attempted_failure_phase(monkeypatch, exc, expected_reason) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._gleif_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=GLEIF_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "gleif_exact_lei")
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is expected_reason
    assert source_run.execution_attempted is True
    assert "GLEIF exact-LEI metadata was temporarily unavailable." in report.warnings
