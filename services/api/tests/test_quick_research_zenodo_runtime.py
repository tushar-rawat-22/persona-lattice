# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderRemoteRateLimitError, ProviderResultValidationError
from app.providers.shared_runtime import DEFAULT_ZENODO_PROVIDER
from app.research import ResearchKind, run_quick_research


RECORD_ID = "8435696"
RECORD_URL = f"https://zenodo.org/records/{RECORD_ID}"


async def _no_public_search(_value: str):
    return ()


async def _no_source(*args, **kwargs):
    return []


def _payload() -> dict[str, object]:
    return {"id": RECORD_ID, "metadata": {"title": "Example preserved research object"}}


@pytest.mark.asyncio
async def test_exact_zenodo_url_executes_shared_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fetcher(record_id: str) -> dict[str, object]:
        assert record_id == RECORD_ID
        return _payload()

    monkeypatch.setattr(DEFAULT_ZENODO_PROVIDER, "fetcher", fetcher)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=RECORD_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    observation = next(item for item in report.observations if item.source == "zenodo_exact_record")
    assert observation.source_locator == RECORD_URL
    assert observation.details["zenodo_record_id"] == RECORD_ID
    assert observation.details["data_license"] == "CC0"
    source_run = next(item for item in report.source_runs if item.source_name == "zenodo_exact_record")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.observation_count == 1
    assert source_run.execution_attempted is True


@pytest.mark.asyncio
async def test_ordinary_url_does_not_attempt_zenodo(monkeypatch: pytest.MonkeyPatch) -> None:
    async def should_not_run(record_id: str):
        raise AssertionError("Zenodo must not run for an ordinary URL")

    monkeypatch.setattr(DEFAULT_ZENODO_PROVIDER, "fetcher", should_not_run)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/page",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    assert all(item.source_name != "zenodo_exact_record" for item in report.source_runs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc,reason",
    [
        (ProviderRemoteRateLimitError("limited", retry_after=4.0), SourceRunReason.REMOTE_RATE_LIMIT),
        (ProviderResultValidationError("bad record"), SourceRunReason.MALFORMED_RESULT),
    ],
)
async def test_zenodo_failures_preserve_attempt_phase(
    monkeypatch: pytest.MonkeyPatch,
    exc: Exception,
    reason: SourceRunReason,
) -> None:
    async def fail(*args, **kwargs):
        raise exc

    monkeypatch.setattr("app.research._zenodo_observations", fail)
    monkeypatch.setattr("app.research._dns_observations", _no_source)
    monkeypatch.setattr("app.research._wayback_observations", _no_source)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value=RECORD_URL,
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "zenodo_exact_record")
    assert source_run.state is SourceRunState.UNAVAILABLE
    assert source_run.reason is reason
    assert source_run.execution_attempted is True
