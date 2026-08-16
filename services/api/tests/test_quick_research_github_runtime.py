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
async def test_production_github_enrichment_path_runs_through_provider_runtime(monkeypatch) -> None:
    class FakeGitHubProvider:
        descriptor = PROVIDER_BY_NAME["github_public_api"]

        def __init__(self) -> None:
            self.values: list[str] = []

        async def execute(self, query, secret):
            self.values.append(query.identifier_value)
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="https://github.com/CaseHandle",
                        payload={
                            "login": "CaseHandle",
                            "html_url": "https://github.com/CaseHandle",
                            "email": "public@example.test",
                            "account_candidate": True,
                            "identity_claim": False,
                            "field_visibility": "public_profile_api",
                        },
                    ),
                )
            )

    github_provider = FakeGitHubProvider()
    monkeypatch.setattr(research_module, "_DEFAULT_GITHUB_PROVIDER", github_provider)
    monkeypatch.setattr(
        research_module,
        "_GITHUB_RUNTIME",
        ProviderRuntime(adapters=[github_provider]),
    )

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="CaseHandle",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    assert github_provider.values == ["CaseHandle"]
    github = [item for item in report.observations if item.source == "github_public_api"]
    assert len(github) == 1
    assert github[0].source_locator == "https://github.com/CaseHandle"
    assert github[0].details["email"] == "public@example.test"
    assert github[0].details["identity_claim"] is False
