# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.errors import ProviderRemoteRateLimitError, ProviderTransientError
from app.providers.registry import PROVIDER_BY_NAME
from app.research import ResearchKind, run_quick_research


async def _no_profile(_value: str):
    return None


async def _github_profile(value: str):
    return {
        "login": value,
        "html_url": f"https://github.com/{value}",
    }


async def _no_public_search(_value: str):
    return ()


def _source(report, name: str):
    return next(record for record in report.source_runs if record.source_name == name)


@pytest.mark.asyncio
async def test_transient_sherlock_failure_keeps_other_username_sources_available() -> None:
    class TransientSherlock:
        descriptor = PROVIDER_BY_NAME["sherlock"]

        async def execute(self, query, secret):
            raise ProviderTransientError("temporary provider outage")

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="runtime-check",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=TransientSherlock(),
        github_lookup=_github_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    sherlock = _source(report, "sherlock")
    assert sherlock.state is SourceRunState.UNAVAILABLE
    assert sherlock.reason is SourceRunReason.EXECUTION_FAILURE
    assert sherlock.execution_attempted is True
    assert any(item.source == "github_public_api" for item in report.observations)
    assert "Sherlock username-site scan did not complete" in report.warnings[0]


@pytest.mark.asyncio
async def test_remote_rate_limited_sherlock_isolated_as_attempted_source_failure() -> None:
    class RateLimitedSherlock:
        descriptor = PROVIDER_BY_NAME["sherlock"]

        async def execute(self, query, secret):
            raise ProviderRemoteRateLimitError("remote provider limit")

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="runtime-check",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=RateLimitedSherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    sherlock = _source(report, "sherlock")
    assert sherlock.state is SourceRunState.UNAVAILABLE
    assert sherlock.reason is SourceRunReason.REMOTE_RATE_LIMIT
    assert sherlock.execution_attempted is True


@pytest.mark.asyncio
async def test_unexpected_post_attempt_sherlock_adapter_failure_is_quarantined() -> None:
    class BrokenSherlock:
        descriptor = PROVIDER_BY_NAME["sherlock"]

        async def execute(self, query, secret):
            raise RuntimeError("synthetic adapter crash")

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="runtime-check",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=BrokenSherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    sherlock = _source(report, "sherlock")
    assert sherlock.state is SourceRunState.UNAVAILABLE
    assert sherlock.reason is SourceRunReason.EXECUTION_FAILURE
    assert sherlock.execution_attempted is True
