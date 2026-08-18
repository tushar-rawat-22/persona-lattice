# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.base import ProviderStatus
from app.providers.bluesky_admission import (
    BlueskyAdmissionError,
    BlueskyPublicWebOptOut,
    admitted_bluesky_profile_fields,
    bluesky_public_web_visibility,
    normalize_bluesky_handle,
)
from app.providers.registry import PROVIDER_BY_NAME


def test_real_world_handle_normalizes_case_without_guessing_generic_usernames() -> None:
    assert normalize_bluesky_handle("Alice.BSKY.SOCIAL") == "alice.bsky.social"
    for value in ("alice", "@alice.bsky.social", " alice.bsky.social", "alice.bsky.social "):
        with pytest.raises(BlueskyAdmissionError):
            normalize_bluesky_handle(value)


def test_reserved_or_non_public_tlds_fail_before_any_future_network_call() -> None:
    for value in (
        "alice.local",
        "alice.internal",
        "alice.example",
        "alice.test",
        "alice.onion",
        "handle.invalid",
    ):
        with pytest.raises(BlueskyAdmissionError):
            normalize_bluesky_handle(value)


def test_public_web_opt_out_is_distinct_from_not_found() -> None:
    payload = {
        "did": "did:plc:abcdefghijklmno",
        "handle": "alice.bsky.social",
        "labels": [{"val": "!no-unauthenticated"}],
    }
    assert bluesky_public_web_visibility(payload) == "opted_out"
    with pytest.raises(BlueskyPublicWebOptOut):
        admitted_bluesky_profile_fields(payload, requested_handle="alice.bsky.social")


def test_malformed_labels_fail_closed_instead_of_erasing_an_opt_out_signal() -> None:
    for labels in ("not-an-array", ["not-an-object"], [{}], [{"val": ""}]):
        with pytest.raises(BlueskyAdmissionError):
            bluesky_public_web_visibility({"labels": labels})


def test_admitted_profile_uses_a_minimal_public_allowlist() -> None:
    result = admitted_bluesky_profile_fields(
        {
            "did": "did:plc:abcdefghijklmno",
            "handle": "Alice.BSKY.SOCIAL",
            "displayName": "Alice Example",
            "description": "intentionally not retained by this source boundary",
            "avatar": "https://cdn.example/avatar.jpg",
            "followersCount": 999999,
            "followsCount": 50,
            "postsCount": 123,
            "viewer": {"muted": False},
            "labels": [{"val": "bot"}],
        },
        requested_handle="alice.bsky.social",
    )
    assert result == {
        "did": "did:plc:abcdefghijklmno",
        "handle": "alice.bsky.social",
        "display_name": "Alice Example",
        "account_candidate": True,
        "identity_claim": False,
        "field_visibility": "public_profile_api",
        "public_web_visibility": "allowed",
    }


def test_returned_handle_must_match_requested_handle() -> None:
    with pytest.raises(BlueskyAdmissionError, match="does not match"):
        admitted_bluesky_profile_fields(
            {"did": "did:plc:abcdefghijklmno", "handle": "mallory.bsky.social"},
            requested_handle="alice.bsky.social",
        )


def test_bluesky_stays_non_executable_until_atomic_activation() -> None:
    source = SOURCE_BY_NAME["bluesky_public_profile"]
    descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]

    assert source.status is SourceStatus.PLANNED
    assert source.source_policy_reviewed is False
    assert source.recursive_eligible is False
    assert descriptor.status == ProviderStatus.PLANNED.value
