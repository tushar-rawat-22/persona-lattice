# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.intelligence.contracts import LeadKind
from app.intelligence.source_evaluation import build_source_evaluation_counters
from app.intelligence.source_outcomes import source_provider_exception_record
from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.providers.base import AuthMode, ProviderQuery, ProviderStatus
from app.providers.bluesky_public import BlueskyPublicProfileProvider
from app.providers.errors import (
    ProviderAccountUnavailableError,
    ProviderPublicWebOptOutError,
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers.registry import PROVIDER_BY_NAME


def _query(value: str = "alice.bsky.social") -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind="username",
        identifier_value=value,
    )


@pytest.mark.asyncio
async def test_bluesky_success_retains_only_reviewed_public_fields() -> None:
    async def fetcher(handle: str):
        assert handle == "alice.bsky.social"
        return {
            "did": "did:plc:abcdefghijklmno",
            "handle": "alice.bsky.social",
            "displayName": "Alice Example",
            "description": "must not be retained",
            "avatar": "https://cdn.example/avatar.jpg",
            "followersCount": 500,
            "labels": [{"val": "bot"}],
        }

    result = await BlueskyPublicProfileProvider(fetcher=fetcher).execute(_query(), None)
    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://bsky.app/profile/alice.bsky.social"
    assert observation.payload == {
        "did": "did:plc:abcdefghijklmno",
        "handle": "alice.bsky.social",
        "display_name": "Alice Example",
        "account_candidate": True,
        "identity_claim": False,
        "field_visibility": "public_profile_api",
        "public_web_visibility": "allowed",
    }


@pytest.mark.asyncio
async def test_bluesky_not_found_returns_empty_result() -> None:
    async def fetcher(_: str):
        return None

    result = await BlueskyPublicProfileProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_bluesky_public_web_opt_out_is_typed_neutral_attempt() -> None:
    async def fetcher(_: str):
        return {
            "did": "did:plc:abcdefghijklmno",
            "handle": "alice.bsky.social",
            "labels": [{"val": "!no-unauthenticated"}],
        }

    with pytest.raises(ProviderPublicWebOptOutError) as captured:
        await BlueskyPublicProfileProvider(fetcher=fetcher).execute(_query(), None)

    record = source_provider_exception_record(
        source_name="bluesky_public_profile",
        lead_kind=LeadKind.USERNAME,
        exc=captured.value,
    )
    assert record is not None
    assert record.state is SourceRunState.WITHHELD
    assert record.reason is SourceRunReason.PUBLIC_WEB_OPT_OUT
    assert record.execution_attempted is True
    counters = build_source_evaluation_counters((record,))["aggregate"]
    assert counters["attempt_count"] == 1
    assert counters["completed_attempt_count"] == 1
    assert counters["failed_attempt_count"] == 0
    assert counters["public_web_opt_out_count"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc",
    [
        ProviderAccountUnavailableError("unavailable"),
        ProviderRemoteRateLimitError(),
        ProviderTransientError("temporary"),
    ],
)
async def test_bluesky_provider_preserves_typed_execution_errors(exc: Exception) -> None:
    async def fetcher(_: str):
        raise exc

    with pytest.raises(type(exc)):
        await BlueskyPublicProfileProvider(fetcher=fetcher).execute(_query(), None)


@pytest.mark.asyncio
async def test_bluesky_malformed_returned_profile_is_post_attempt_validation() -> None:
    async def fetcher(_: str):
        return {"did": "did:plc:abcdefghijklmno", "handle": "mallory.bsky.social"}

    with pytest.raises(ProviderResultValidationError):
        await BlueskyPublicProfileProvider(fetcher=fetcher).execute(_query(), None)


@pytest.mark.asyncio
async def test_bluesky_rejects_generic_username_and_credentials_before_fetch() -> None:
    called = False

    async def fetcher(_: str):
        nonlocal called
        called = True
        return None

    provider = BlueskyPublicProfileProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError):
        await provider.execute(_query("alice"), None)
    with pytest.raises(ProviderValidationError):
        await provider.execute(_query(), "unexpected-secret")
    assert called is False


def test_bluesky_descriptor_is_active_without_credentials_and_remains_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]

    assert descriptor.status == ProviderStatus.DEVELOPMENT.value
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.secret_env is None
    assert descriptor.supported_identifier_kinds == frozenset({"username"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 64 * 1024
    assert descriptor.max_concurrency == 2
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0
