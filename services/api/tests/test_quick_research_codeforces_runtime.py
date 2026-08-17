# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.models import Purpose
from app.providers import ProviderObservationData, ProviderResult, ProviderRuntime
from app.providers.registry import PROVIDER_BY_NAME
from app.research import ResearchKind, run_quick_research
import app.research as research_module


class _EmptySherlock:
    descriptor = PROVIDER_BY_NAME["sherlock"]

    async def execute(self, query, secret):
        return ProviderResult(observations=())


async def _no_profile(_value: str):
    return None


async def _no_public_search(_value: str):
    return ()


@pytest.mark.asyncio
async def test_production_codeforces_path_runs_through_shared_provider_runtime(monkeypatch) -> None:
    class FakeCodeforcesProvider:
        descriptor = PROVIDER_BY_NAME["codeforces_public_api"]

        def __init__(self) -> None:
            self.queries: list[tuple[str, str]] = []

        async def execute(self, query, secret):
            self.queries.append((query.identifier_kind, query.identifier_value))
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="https://codeforces.com/profile/CaseHandle",
                        payload={
                            "handle": "CaseHandle",
                            "matched_by": "exact_handle",
                            "account_candidate": True,
                            "identity_claim": False,
                            "field_visibility": "public_profile_api",
                        },
                    ),
                )
            )

    codeforces_provider = FakeCodeforcesProvider()
    runtime = ProviderRuntime(adapters=[codeforces_provider])
    monkeypatch.setattr(research_module, "DEFAULT_CODEFORCES_PROVIDER", codeforces_provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

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

    assert codeforces_provider.queries == [("username", "CaseHandle")]
    observations = [item for item in report.observations if item.source == "codeforces_public_api"]
    assert len(observations) == 1
    assert observations[0].source_locator == "https://codeforces.com/profile/CaseHandle"
    assert observations[0].details["matched_by"] == "exact_handle"
    assert observations[0].details["identity_claim"] is False
