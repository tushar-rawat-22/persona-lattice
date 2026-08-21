# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers import ProviderObservationData, ProviderResult, ProviderRuntime
from app.providers.gitlab_public import GitLabPublicProfileProvider
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
@pytest.mark.parametrize(
    ("kind", "value", "matched_by"),
    [
        (ResearchKind.USERNAME, "CaseHandle", "username"),
        (ResearchKind.EMAIL, "public@example.test", "exact_public_email"),
    ],
)
async def test_production_gitlab_paths_run_through_shared_provider_runtime(
    monkeypatch,
    kind: ResearchKind,
    value: str,
    matched_by: str,
) -> None:
    class FakeGitLabProvider:
        descriptor = PROVIDER_BY_NAME["gitlab_public_api"]

        def __init__(self) -> None:
            self.queries: list[tuple[str, str]] = []

        async def execute(self, query, secret):
            self.queries.append((query.identifier_kind, query.identifier_value))
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="https://gitlab.com/CaseHandle",
                        payload={
                            "username": "CaseHandle",
                            "public_email": "public@example.test",
                            "web_url": "https://gitlab.com/CaseHandle",
                            "matched_by": matched_by,
                            "account_candidate": True,
                            "identity_claim": False,
                            "field_visibility": "public_profile_api",
                        },
                    ),
                )
            )

    gitlab_provider = FakeGitLabProvider()
    runtime = ProviderRuntime(adapters=[gitlab_provider])
    monkeypatch.setattr(research_module, "DEFAULT_GITLAB_PROVIDER", gitlab_provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

    kwargs = {
        "kind": kind,
        "value": value,
        "purpose": Purpose.SELF_AUDIT,
        "consent_acknowledged": True,
        "public_search_lookup": _no_public_search,
    }
    if kind is ResearchKind.USERNAME:
        kwargs.update(
            {
                "sherlock_provider": _EmptySherlock(),
                "github_lookup": _no_profile,
                "codeforces_lookup": _no_profile,
            }
        )

    report = await run_quick_research(**kwargs)

    expected_kind = "username" if kind is ResearchKind.USERNAME else "email"
    assert gitlab_provider.queries == [(expected_kind, value)]
    gitlab = [item for item in report.observations if item.source == "gitlab_public_api"]
    assert len(gitlab) == 1
    assert gitlab[0].source_locator == "https://gitlab.com/CaseHandle"
    assert gitlab[0].details["matched_by"] == matched_by
    assert gitlab[0].details["identity_claim"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "value"),
    [
        (ResearchKind.USERNAME, "gitlab-bot-handle"),
        (ResearchKind.EMAIL, "bot@example.test"),
    ],
)
async def test_gitlab_human_filtered_empty_result_is_attempted_no_match(
    monkeypatch,
    kind: ResearchKind,
    value: str,
) -> None:
    async def no_human_match(fetch_kind: str, fetch_value: str):
        expected_kind = "username" if kind is ResearchKind.USERNAME else "email"
        assert (fetch_kind, fetch_value) == (expected_kind, value)
        return None

    gitlab_provider = GitLabPublicProfileProvider(fetcher=no_human_match)
    runtime = ProviderRuntime(adapters=[gitlab_provider])
    monkeypatch.setattr(research_module, "DEFAULT_GITLAB_PROVIDER", gitlab_provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

    kwargs = {
        "kind": kind,
        "value": value,
        "purpose": Purpose.PUBLIC_SOURCE_RESEARCH,
        "consent_acknowledged": True,
        "public_search_lookup": _no_public_search,
    }
    if kind is ResearchKind.USERNAME:
        kwargs.update(
            {
                "sherlock_provider": _EmptySherlock(),
                "github_lookup": _no_profile,
                "codeforces_lookup": _no_profile,
            }
        )

    report = await run_quick_research(**kwargs)

    assert [item for item in report.observations if item.source == "gitlab_public_api"] == []
    gitlab_runs = [item for item in report.source_runs if item.source_name == "gitlab_public_api"]
    assert len(gitlab_runs) == 1
    assert gitlab_runs[0].state is SourceRunState.NOT_FOUND
    assert gitlab_runs[0].reason is SourceRunReason.NO_MATCH
    assert gitlab_runs[0].execution_attempted is True
    assert gitlab_runs[0].observation_count == 0