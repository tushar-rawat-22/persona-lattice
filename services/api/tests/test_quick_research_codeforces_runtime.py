# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers import ProviderResult
from app.providers.registry import PROVIDER_BY_NAME
from app.research import ResearchKind, run_quick_research


class _EmptySherlock:
    descriptor = PROVIDER_BY_NAME["sherlock"]

    async def execute(self, query, secret):
        return ProviderResult(observations=())


async def _no_profile(_value: str):
    return None


async def _no_public_search(_value: str):
    return ()


@pytest.mark.asyncio
async def test_production_codeforces_path_is_policy_blocked_without_provider_attempt() -> None:
    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="CaseHandle",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    assert [item for item in report.observations if item.source == "codeforces_public_api"] == []
    codeforces_runs = [
        item for item in report.source_runs if item.source_name == "codeforces_public_api"
    ]
    assert len(codeforces_runs) == 1
    assert codeforces_runs[0].state is SourceRunState.BLOCKED
    assert codeforces_runs[0].reason is SourceRunReason.PROVIDER_POLICY
    assert codeforces_runs[0].execution_attempted is False
    assert codeforces_runs[0].observation_count == 0
