# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderResultValidationError, ProviderRemoteRateLimitError
from app.providers.shared_runtime import DEFAULT_WIKIDATA_PROVIDER
from app.research import ResearchKind, run_quick_research


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


@pytest.mark.asyncio
async def test_exact_wikidata_url_executes_shared_runtime(monkeypatch) -> None:
    async def fetcher(entity_id: str) -> dict[str, object]:
        assert entity_id == "Q42"
        return {
            "entities": {
                "Q42": {
                    "id": "Q42",
                    "type": "item",
                    "labels": {"en": {"language": "en", "value": "Douglas Adams"}},
                    "descriptions": {"en": {"language": "en", "value": "English writer and humorist"}},
                }
            }
        }

    monkeypatch.setattr(DEFAULT_WIKIDATA_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://www.wikidata.org/wiki/Q42",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(item for item in report.observations if item.source == "wikidata_exact_entity")
    assert observation.source_locator == "https://www.wikidata.org/wiki/Q42"
    assert observation.details["wikidata_entity_id"] == "Q42"
    assert observation.details["data_license"] == "CC0"
    assert observation.details["identity_claim"] is False
    source_run = next(item for item in report.source_runs if item.source_name == "wikidata_exact_entity")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_wikidata_provider(monkeypatch) -> None:
    async def should_not_run(entity_id: str):
        raise AssertionError("Wikidata provider must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_WIKIDATA_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/public-page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )
    assert all(item.source != "wikidata_exact_entity" for item in report.observations)
    assert all(item.source_name != "wikidata_exact_entity" for item in report.source_runs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exc", "expected_reason"),
    [
        (ProviderRemoteRateLimitError("remote limit", retry_after=3.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad returned entity"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_wikidata_runtime_preserves_attempted_failure_phase(monkeypatch, exc, expected_reason) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._wikidata_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://www.wikidata.org/wiki/Q42",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "wikidata_exact_entity")
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is expected_reason
    assert source_run.execution_attempted is True
    assert "Wikidata exact-entity metadata was temporarily unavailable." in report.warnings
