# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.models import Purpose
from app.providers import ProviderObservationData, ProviderResult, ProviderRuntime
from app.providers.errors import ProviderResultValidationError
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
async def test_canonical_keybase_username_runs_through_shared_runtime(monkeypatch) -> None:
    class FakeKeybaseProvider:
        descriptor = PROVIDER_BY_NAME["keybase_public_user"]

        def __init__(self) -> None:
            self.values: list[str] = []

        async def execute(self, query, secret):
            self.values.append(query.identifier_value)
            return ProviderResult(
                observations=(
                    ProviderObservationData(
                        source_locator="https://keybase.io/maxtaco",
                        payload={
                            "keybase_username": "maxtaco",
                            "keybase_uid": "9a2c8a8ac48162723c7992570c87da00",
                            "account_created_at": 1399919269,
                            "account_candidate": True,
                            "identity_claim": False,
                            "field_visibility": "public_directory_basics",
                        },
                    ),
                )
            )

    provider = FakeKeybaseProvider()
    monkeypatch.setattr(research_module, "DEFAULT_KEYBASE_PROVIDER", provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", ProviderRuntime(adapters=[provider]))

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="maxtaco",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    assert provider.values == ["maxtaco"]
    keybase = [item for item in report.observations if item.source == "keybase_public_user"]
    assert len(keybase) == 1
    assert keybase[0].source_locator == "https://keybase.io/maxtaco"
    assert keybase[0].details["identity_claim"] is False
    source_run = next(item for item in report.source_runs if item.source_name == "keybase_public_user")
    assert source_run.attempt_count == 1
    assert source_run.observation_count == 1


@pytest.mark.asyncio
async def test_noncanonical_username_never_attempts_keybase(monkeypatch) -> None:
    class FailingIfCalled:
        descriptor = PROVIDER_BY_NAME["keybase_public_user"]

        async def execute(self, query, secret):
            raise AssertionError("Keybase should not run for noncanonical usernames")

    provider = FailingIfCalled()
    monkeypatch.setattr(research_module, "DEFAULT_KEYBASE_PROVIDER", provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", ProviderRuntime(adapters=[provider]))

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="CaseHandle",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    assert all(item.source_name != "keybase_public_user" for item in report.source_runs)


@pytest.mark.asyncio
async def test_post_attempt_keybase_validation_failure_is_reported(monkeypatch) -> None:
    class MalformedKeybase:
        descriptor = PROVIDER_BY_NAME["keybase_public_user"]

        async def execute(self, query, secret):
            raise ProviderResultValidationError("malformed public basics")

    provider = MalformedKeybase()
    monkeypatch.setattr(research_module, "DEFAULT_KEYBASE_PROVIDER", provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", ProviderRuntime(adapters=[provider]))

    report = await run_quick_research(
        kind=ResearchKind.USERNAME,
        value="maxtaco",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        sherlock_provider=_EmptySherlock(),
        github_lookup=_no_profile,
        gitlab_lookup=_no_profile,
        codeforces_lookup=_no_profile,
        public_search_lookup=_no_public_search,
    )

    assert "Keybase public account basics were temporarily unavailable." in report.warnings
    source_run = next(item for item in report.source_runs if item.source_name == "keybase_public_user")
    assert source_run.attempt_count == 1
    assert source_run.failed_attempt_count == 1
