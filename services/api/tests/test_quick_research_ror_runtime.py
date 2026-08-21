# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderResultValidationError, ProviderRemoteRateLimitError
from app.providers.shared_runtime import DEFAULT_ROR_PROVIDER
from app.research import ResearchKind, run_quick_research


ROR_ID = "015w2mp89"
ROR_URL = f"https://ror.org/{ROR_ID}"


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


def _payload() -> dict[str, object]:
    return {
        "id": ROR_URL,
        "status": "active",
        "names": [
            {
                "lang": "en",
                "types": ["ror_display", "label"],
                "value": "Example Research Institute",
            }
        ],
        "types": ["education"],
    }


@pytest.mark.asyncio
async def test_exact_ror_url_executes_shared_runtime(monkeypatch) -> None:
    async def fetcher(ror_id: str) -> dict[str, object]:
        assert ror_id == ROR_ID
        return _payload()

    monkeypatch.setattr(DEFAULT_ROR_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=ROR_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(item for item in report.observations if item.source == "ror_exact_organization")
    assert observation.source_locator == ROR_URL
    assert observation.details["ror_id"] == ROR_URL
    assert observation.details["ror_display_name"] == "Example Research Institute"
    assert observation.details["data_license"] == "CC0"
    assert observation.details["identity_claim"] is False
    source_run = next(item for item in report.source_runs if item.source_name == "ror_exact_organization")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_ror_provider(monkeypatch) -> None:
    async def should_not_run(ror_id: str):
        raise AssertionError("ROR provider must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_ROR_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )
    assert all(item.source != "ror_exact_organization" for item in report.observations)
    assert all(item.source_name != "ror_exact_organization" for item in report.source_runs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "expected_reason"),
    [
        (ProviderRemoteRateLimitError("remote limit", retry_after=3.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad returned organization"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_ror_runtime_preserves_attempted_failure_phase(monkeypatch, exc, expected_reason) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._ror_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=ROR_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "ror_exact_organization")
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is expected_reason
    assert source_run.execution_attempted is True
    assert "ROR exact-organization metadata was temporarily unavailable." in report.warnings
