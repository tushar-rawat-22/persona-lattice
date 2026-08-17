# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers import ProviderResult
from app.providers.errors import ProviderRateBudgetExceeded, ProviderRemoteRateLimitError
from app.providers.registry import PROVIDER_BY_NAME
from app.research import ResearchKind, run_quick_research


async def _no_profile(_value: str):
    return None


async def _no_public_search(_value: str):
    return ()


class _EmptySherlock:
    descriptor = PROVIDER_BY_NAME["sherlock"]

    async def execute(self, query, secret):
        return ProviderResult(observations=())


@pytest.mark.asyncio
async def test_username_quick_research_records_completed_zero_result_sources() -> None:
    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="CaseSensitiveHandle",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    by_source = {record.source_name: record for record in report.source_runs}

    assert set(by_source) == {
        "sherlock",
        "github_public_api",
        "gitlab_public_api",
        "codeforces_public_api",
        "brave_public_web_index",
    }
    assert all(record.state is SourceRunState.NOT_FOUND for record in by_source.values())
    assert all(record.reason is SourceRunReason.NO_MATCH for record in by_source.values())
    assert all(record.execution_attempted for record in by_source.values())


@pytest.mark.asyncio
async def test_unconfigured_optional_search_is_not_reported_as_not_found(monkeypatch) -> None:
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    report = await run_quick_research(
        kind=ResearchKind.PHONE,
        value="+14155552671",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
    )

    by_source = {record.source_name: record for record in report.source_runs}
    local = by_source["libphonenumber_metadata"]
    search = by_source["brave_public_web_index"]

    assert local.state is SourceRunState.EXECUTED
    assert local.observation_count == 1
    assert local.execution_attempted is True
    assert search.state is SourceRunState.UNAVAILABLE
    assert search.reason is SourceRunReason.OPTIONAL_NOT_CONFIGURED
    assert search.execution_attempted is False


@pytest.mark.asyncio
async def test_injected_local_budget_stop_is_preserved_as_pre_call_state() -> None:
    async def local_budget(_value: str):
        raise ProviderRateBudgetExceeded("test budget")

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="budget-check",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=local_budget,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    github = next(record for record in report.source_runs if record.source_name == "github_public_api")
    assert github.state is SourceRunState.BUDGET_STOPPED
    assert github.reason is SourceRunReason.LOCAL_BUDGET
    assert github.execution_attempted is False


@pytest.mark.asyncio
async def test_injected_remote_rate_limit_is_an_attempted_unavailable_state() -> None:
    async def remote_limit(_value: str):
        raise ProviderRemoteRateLimitError("test remote limit")

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="remote-check",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=remote_limit,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    github = next(record for record in report.source_runs if record.source_name == "github_public_api")
    assert github.state is SourceRunState.UNAVAILABLE
    assert github.reason is SourceRunReason.REMOTE_RATE_LIMIT
    assert github.execution_attempted is True
