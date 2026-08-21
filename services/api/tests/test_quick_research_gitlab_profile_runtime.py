# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.models import Purpose
from app.providers import ProviderObservationData, ProviderResult, ProviderRuntime
from app.providers.registry import PROVIDER_BY_NAME
from app.research import ResearchKind, run_quick_research
import app.research as research_module


async def _no_public_search(_value: str):
    return ()


async def _no_network(_value: str):
    return ()


@pytest.mark.asyncio
async def test_exact_gitlab_profile_url_uses_existing_shared_gitlab_runtime(monkeypatch) -> None:
    class FakeGitLabProvider:
        descriptor = PROVIDER_BY_NAME["gitlab_public_api"]

        def __init__(self) -> None:
            self.queries: list[tuple[str, str]] = []

        async def execute(self, query, secret):
            self.queries.append((query.identifier_kind, query.identifier_value))
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="https://gitlab.com/Alice",
                        payload={
                            "id": 7,
                            "username": "Alice",
                            "name": "Alice Example",
                            "web_url": "https://gitlab.com/Alice",
                            "account_candidate": True,
                            "identity_claim": False,
                            "field_visibility": "public_profile_api",
                            "matched_by": "exact_profile_url",
                        },
                    ),
                )
            )

    gitlab_provider = FakeGitLabProvider()
    runtime = ProviderRuntime(adapters=[gitlab_provider])
    monkeypatch.setattr(research_module, "DEFAULT_GITLAB_PROVIDER", gitlab_provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://gitlab.com/Alice",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
        network_lookup=_no_network,
    )

    assert gitlab_provider.queries == [("url", "https://gitlab.com/Alice")]
    gitlab = [item for item in report.observations if item.source == "gitlab_public_api"]
    assert len(gitlab) == 1
    assert gitlab[0].source_locator == "https://gitlab.com/Alice"
    assert gitlab[0].details["matched_by"] == "exact_profile_url"
    assert gitlab[0].details["account_candidate"] is True
    assert gitlab[0].details["identity_claim"] is False
    runs = [item for item in report.source_runs if item.source_name == "gitlab_public_api"]
    assert len(runs) == 1
    assert runs[0].lead_kind.value == "url"


@pytest.mark.asyncio
async def test_reserved_gitlab_profile_route_does_not_attempt_gitlab_provider(monkeypatch) -> None:
    class FailingGitLabProvider:
        descriptor = PROVIDER_BY_NAME["gitlab_public_api"]

        async def execute(self, query, secret):
            raise AssertionError("GitLab provider must not run for a reserved top-level route")

    gitlab_provider = FailingGitLabProvider()
    runtime = ProviderRuntime(adapters=[gitlab_provider])
    monkeypatch.setattr(research_module, "DEFAULT_GITLAB_PROVIDER", gitlab_provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://gitlab.com/search",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
        network_lookup=_no_network,
    )

    assert not [item for item in report.source_runs if item.source_name == "gitlab_public_api"]
    assert not [item for item in report.observations if item.source == "gitlab_public_api"]
