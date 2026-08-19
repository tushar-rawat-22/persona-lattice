# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib

import pytest

from app.intelligence.source_bindings import SourceBindingError, source_binding_for
from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.gravatar_admission import (
    GravatarAdmissionError,
    admitted_gravatar_profile_fields,
    gravatar_profile_identifier,
)


def test_gravatar_identifier_uses_provider_required_trim_lowercase_sha256() -> None:
    expected = hashlib.sha256(b"alice@example.com").hexdigest()
    assert gravatar_profile_identifier(" Alice@Example.COM ") == expected


def test_gravatar_identifier_rejects_malformed_email_seed() -> None:
    for value in ("", "alice", "@example.com", "alice@"):
        with pytest.raises(GravatarAdmissionError):
            gravatar_profile_identifier(value)


def test_admitted_profile_keeps_only_minimal_reviewed_fields() -> None:
    email = "alice@example.com"
    result = admitted_gravatar_profile_fields(
        {
            "hash": gravatar_profile_identifier(email),
            "profile_url": "https://gravatar.com/alice",
            "display_name": "Alice Example",
            "location": "not retained",
            "company": "not retained",
            "description": "not retained",
            "verified_accounts": [{"url": "https://social.example/alice"}],
            "contact_info": {"email": "private@example.com"},
            "payments": [{"label": "not retained"}],
            "avatar_url": "https://gravatar.com/avatar/ignored",
        },
        requested_email=email,
    )
    assert result == (
        "https://gravatar.com/alice",
        {
            "display_name": "Alice Example",
            "account_candidate": True,
            "identity_claim": False,
            "field_visibility": "public_profile_api",
        },
    )


def test_returned_hash_must_match_requested_email() -> None:
    with pytest.raises(GravatarAdmissionError, match="does not match"):
        admitted_gravatar_profile_fields(
            {
                "hash": gravatar_profile_identifier("mallory@example.com"),
                "profile_url": "https://gravatar.com/mallory",
            },
            requested_email="alice@example.com",
        )


@pytest.mark.parametrize(
    "profile_url",
    [
        "http://gravatar.com/alice",
        "https://example.com/alice",
        "https://user@gravatar.com/alice",
        "https://gravatar.com/alice?tracking=1",
        "https://gravatar.com/alice#fragment",
        "https://gravatar.com/a/b",
        "https://gravatar.com/",
    ],
)
def test_profile_locator_is_strict_public_gravatar_provenance(profile_url: str) -> None:
    with pytest.raises(GravatarAdmissionError):
        admitted_gravatar_profile_fields(
            {
                "hash": gravatar_profile_identifier("alice@example.com"),
                "profile_url": profile_url,
            },
            requested_email="alice@example.com",
        )


def test_gravatar_remains_planned_and_unbound_until_terms_requirements_are_met() -> None:
    source = SOURCE_BY_NAME["gravatar_public_profile"]
    assert source.status is SourceStatus.PLANNED
    assert source.source_policy_reviewed is False
    assert source.recursive_eligible is False
    with pytest.raises(SourceBindingError, match="no executable runtime binding"):
        source_binding_for("gravatar_public_profile")
