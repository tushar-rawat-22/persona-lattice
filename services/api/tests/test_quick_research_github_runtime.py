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


async def _no_network(_value: str):
    return ()


@pytest.mark.asyncio
async def test_production_github_enrichment_path_runs_through_shared_provider_runtime(
    monkeypatch,
) -> None:
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
    runtime = ProviderRuntime(adapters=[github_provider])
    monkeypatch.setattr(research_module, "DEFAULT_GITHUB_PROVIDER", github_provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

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


@pytest.mark.asyncio
async def test_exact_github_repository_url_uses_same_shared_provider_runtime(
    monkeypatch,
) -> None:
    class FakeGitHubProvider:
        descriptor = PROVIDER_BY_NAME["github_public_api"]

        def __init__(self) -> None:
            self.queries: list[tuple[str, str]] = []

        async def execute(self, query, secret):
            self.queries.append((query.identifier_kind, query.identifier_value))
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="https://github.com/openai/openai-python",
                        payload={
                            "github_repository_full_name": "openai/openai-python",
                            "github_repository_owner_login": "openai",
                            "github_repository_owner_type": "Organization",
                            "github_repository_private": False,
                            "github_repository_fork": False,
                            "github_repository_archived": False,
                            "identity_claim": False,
                            "field_visibility": "public_repository_api",
                        },
                    ),
                )
            )

    github_provider = FakeGitHubProvider()
    runtime = ProviderRuntime(adapters=[github_provider])
    monkeypatch.setattr(research_module, "DEFAULT_GITHUB_PROVIDER", github_provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://github.com/openai/openai-python",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
        network_lookup=_no_network,
    )

    assert github_provider.queries == [("url", "https://github.com/openai/openai-python")]
    github = [item for item in report.observations if item.source == "github_public_api"]
    assert len(github) == 1
    assert github[0].source_locator == "https://github.com/openai/openai-python"
    assert github[0].details["github_repository_owner_type"] == "Organization"
    assert github[0].details["identity_claim"] is False
    github_runs = [item for item in report.source_runs if item.source_name == "github_public_api"]
    assert len(github_runs) == 1
    assert github_runs[0].lead_kind.value == "url"
