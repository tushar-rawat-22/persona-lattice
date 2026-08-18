# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

import app.research as research_module
from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers import ProviderObservationData, ProviderResult, ProviderRuntime
from app.providers.errors import ProviderPublicWebOptOutError
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
async def test_plain_username_is_not_applicable_to_bluesky_and_never_calls_runtime(
    monkeypatch,
) -> None:
    class UnexpectedRuntime:
        async def execute(self, *, request, query):
            raise AssertionError(f"unexpected governed call to {request.provider_name}")

    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", UnexpectedRuntime())

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="plainhandle",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    assert not any(item.source == "bluesky_public_profile" for item in report.observations)
    assert not any(item.source_name == "bluesky_public_profile" for item in report.source_runs)


@pytest.mark.asyncio
async def test_valid_at_handle_runs_bluesky_through_governed_runtime(monkeypatch) -> None:
    class FakeBlueskyProvider:
        descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]

        def __init__(self) -> None:
            self.values: list[str] = []

        async def execute(self, query, secret):
            self.values.append(query.identifier_value)
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="https://bsky.app/profile/alice.bsky.social",
                        payload={
                            "did": "did:plc:alice",
                            "handle": "alice.bsky.social",
                            "display_name": "Alice",
                            "account_candidate": True,
                            "identity_claim": False,
                            "field_visibility": "public_profile_api",
                            "public_web_visibility": "allowed",
                        },
                    ),
                )
            )

    provider = FakeBlueskyProvider()
    runtime = ProviderRuntime(adapters=[provider])
    monkeypatch.setattr(research_module, "DEFAULT_BLUESKY_PROVIDER", provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="Alice.Bsky.Social",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    assert provider.values == ["alice.bsky.social"]
    observations = [item for item in report.observations if item.source == "bluesky_public_profile"]
    assert len(observations) == 1
    assert observations[0].source_locator == "https://bsky.app/profile/alice.bsky.social"
    assert observations[0].details["did"] == "did:plc:alice"
    assert observations[0].details["identity_claim"] is False

    source_run = next(
        item for item in report.source_runs if item.source_name == "bluesky_public_profile"
    )
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.reason is SourceRunReason.RESULTS_RETURNED
    assert source_run.observation_count == 1


@pytest.mark.asyncio
async def test_bluesky_public_web_opt_out_is_withheld_without_failure_warning(monkeypatch) -> None:
    class OptedOutBlueskyProvider:
        descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]

        async def execute(self, query, secret):
            raise ProviderPublicWebOptOutError(
                "Bluesky profile opted out of unauthenticated public-web use."
            )

    provider = OptedOutBlueskyProvider()
    runtime = ProviderRuntime(adapters=[provider])
    monkeypatch.setattr(research_module, "DEFAULT_BLUESKY_PROVIDER", provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="alice.bsky.social",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    source_run = next(
        item for item in report.source_runs if item.source_name == "bluesky_public_profile"
    )
    assert source_run.state is SourceRunState.WITHHELD
    assert source_run.reason is SourceRunReason.PUBLIC_WEB_OPT_OUT
    assert not any("Bluesky" in warning for warning in report.warnings)
