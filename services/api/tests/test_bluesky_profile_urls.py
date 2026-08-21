# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

import app.research as research_module
from app.intelligence.contracts import LeadKind
from app.intelligence.source_bindings import SOURCE_BINDING_BY_NAME
from app.intelligence.source_catalog import SOURCE_BY_NAME
from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers import ProviderObservationData, ProviderQuery, ProviderResult, ProviderRuntime
from app.providers.bluesky_public import BlueskyPublicProfileProvider, bluesky_profile_handle_from_url
from app.providers.errors import ProviderPublicWebOptOutError, ProviderValidationError
from app.providers.registry import PROVIDER_BY_NAME
from app.research import ResearchKind, run_quick_research


def test_exact_bluesky_handle_profile_url_admission_is_fail_closed() -> None:
    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.bsky.social") == "alice.bsky.social"
    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.bsky.social/") is None
    assert bluesky_profile_handle_from_url("https://bsky.app/profile/Alice.Bsky.Social") is None
    assert bluesky_profile_handle_from_url("https://bsky.app/profile/did:plc:abc") is None
    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.bsky.social/post/3abc") is None
    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice%2Ebsky.social") is None
    assert bluesky_profile_handle_from_url("http://bsky.app/profile/alice.bsky.social") is None
    assert bluesky_profile_handle_from_url("https://user@bsky.app/profile/alice.bsky.social") is None
    assert bluesky_profile_handle_from_url("https://bsky.app:443/profile/alice.bsky.social") is None
    assert bluesky_profile_handle_from_url("https://bsky.app:bad/profile/alice.bsky.social") is None
    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.bsky.social?x=1") is None
    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.test") is None


@pytest.mark.asyncio
async def test_provider_reuses_handle_lookup_for_exact_profile_url() -> None:
    seen: list[str] = []

    async def fetcher(handle: str):
        seen.append(handle)
        return {
            "did": "did:plc:alice",
            "handle": "alice.bsky.social",
            "displayName": "Alice",
        }

    provider = BlueskyPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(
        ProviderQuery(
            subject_id=uuid4(),
            identifier_id=uuid4(),
            identifier_kind="url",
            identifier_value="https://bsky.app/profile/alice.bsky.social",
        ),
        None,
    )
    assert seen == ["alice.bsky.social"]
    assert len(result.observations) == 1
    assert result.observations[0].source_locator == "https://bsky.app/profile/alice.bsky.social"
    assert result.observations[0].payload["identity_claim"] is False


@pytest.mark.asyncio
async def test_provider_url_no_match_is_clean_after_one_fetch() -> None:
    seen: list[str] = []

    async def fetcher(handle: str):
        seen.append(handle)
        return None

    provider = BlueskyPublicProfileProvider(fetcher=fetcher)
    result = await provider.execute(
        ProviderQuery(
            subject_id=uuid4(),
            identifier_id=uuid4(),
            identifier_kind="url",
            identifier_value="https://bsky.app/profile/alice.bsky.social",
        ),
        None,
    )
    assert seen == ["alice.bsky.social"]
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_did_and_post_urls_without_fetch() -> None:
    async def unexpected(_handle: str):
        raise AssertionError("provider must not fetch non-applicable Bluesky URL")

    provider = BlueskyPublicProfileProvider(fetcher=unexpected)
    for value in (
        "https://bsky.app/profile/did:plc:abc",
        "https://bsky.app/profile/alice.bsky.social/post/3abc",
    ):
        with pytest.raises(ProviderValidationError):
            await provider.execute(
                ProviderQuery(
                    subject_id=uuid4(),
                    identifier_id=uuid4(),
                    identifier_kind="url",
                    identifier_value=value,
                ),
                None,
            )


def test_catalog_binding_and_descriptor_share_username_url_contract() -> None:
    assert SOURCE_BY_NAME["bluesky_public_profile"].accepts == frozenset({LeadKind.USERNAME, LeadKind.URL})
    assert SOURCE_BINDING_BY_NAME["bluesky_public_profile"].accepts == frozenset({LeadKind.USERNAME, LeadKind.URL})
    assert PROVIDER_BY_NAME["bluesky_public_profile"].supported_identifier_kinds == frozenset({"username", "url"})
    descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0


async def _no_dns(*args, **kwargs):
    return []


async def _no_wayback(*args, **kwargs):
    return []


async def _no_search(_value: str):
    return ()


@pytest.mark.asyncio
async def test_exact_profile_url_runs_bluesky_once_through_shared_runtime(monkeypatch) -> None:
    class FakeBlueskyProvider:
        descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]

        def __init__(self) -> None:
            self.queries = []

        async def execute(self, query, secret):
            self.queries.append(query)
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
    monkeypatch.setattr(research_module, "_dns_observations", _no_dns)
    monkeypatch.setattr(research_module, "_wayback_observations", _no_wayback)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://bsky.app/profile/alice.bsky.social",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_search,
    )

    assert len(provider.queries) == 1
    assert provider.queries[0].identifier_kind == "url"
    assert provider.queries[0].identifier_value == "https://bsky.app/profile/alice.bsky.social"
    observations = [item for item in report.observations if item.source == "bluesky_public_profile"]
    assert len(observations) == 1
    source_run = next(item for item in report.source_runs if item.source_name == "bluesky_public_profile")
    assert source_run.state is SourceRunState.EXECUTED
    assert source_run.reason is SourceRunReason.RESULTS_RETURNED
    assert source_run.observation_count == 1


@pytest.mark.asyncio
async def test_exact_profile_url_preserves_public_web_opt_out_as_neutral_withheld(monkeypatch) -> None:
    class OptedOutProvider:
        descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]

        async def execute(self, query, secret):
            raise ProviderPublicWebOptOutError("opted out")

    provider = OptedOutProvider()
    runtime = ProviderRuntime(adapters=[provider])
    monkeypatch.setattr(research_module, "DEFAULT_BLUESKY_PROVIDER", provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)
    monkeypatch.setattr(research_module, "_dns_observations", _no_dns)
    monkeypatch.setattr(research_module, "_wayback_observations", _no_wayback)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://bsky.app/profile/alice.bsky.social",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "bluesky_public_profile")
    assert source_run.state is SourceRunState.WITHHELD
    assert source_run.reason is SourceRunReason.PUBLIC_WEB_OPT_OUT
    assert source_run.execution_attempted is True
    assert not any("Bluesky exact public-profile" in warning for warning in report.warnings)


@pytest.mark.asyncio
async def test_exact_profile_url_no_match_is_typed_not_found(monkeypatch) -> None:
    class NoMatchProvider:
        descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]

        async def execute(self, query, secret):
            return ProviderResult(observations=())

    provider = NoMatchProvider()
    runtime = ProviderRuntime(adapters=[provider])
    monkeypatch.setattr(research_module, "DEFAULT_BLUESKY_PROVIDER", provider)
    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)
    monkeypatch.setattr(research_module, "_dns_observations", _no_dns)
    monkeypatch.setattr(research_module, "_wayback_observations", _no_wayback)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://bsky.app/profile/alice.bsky.social",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_search,
    )

    source_run = next(item for item in report.source_runs if item.source_name == "bluesky_public_profile")
    assert source_run.state is SourceRunState.NOT_FOUND
    assert source_run.reason is SourceRunReason.NO_MATCH
    assert source_run.execution_attempted is True
