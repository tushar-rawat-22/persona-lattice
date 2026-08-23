# SPDX-License-Identifier: Apache-2.0
import pytest

from app.evidence import (
    IdentifierKind,
    InvalidIdentifier,
    normalize_collection,
    normalize_identifier,
)


def test_phone_normalizes_to_e164() -> None:
    result = normalize_identifier(IdentifierKind.PHONE, "+91 98765 43210")
    assert result.normalized_value == "+919876543210"
    assert result.comparison_key == "+919876543210"


def test_email_and_username_normalization_is_conservative() -> None:
    email = normalize_identifier(IdentifierKind.EMAIL, " Test@Example.COM ")
    username = normalize_identifier(IdentifierKind.USERNAME, " @Demo_User ")

    assert email.normalized_value == "Test@example.com"
    assert email.comparison_key == "Test@example.com"
    assert username.normalized_value == "Demo_User"
    assert username.comparison_key == "Demo_User"


def test_case_variants_are_not_merged_without_provider_specific_rules() -> None:
    emails, email_warnings = normalize_collection(
        IdentifierKind.EMAIL,
        ["User@example.com", "user@example.com"],
    )
    usernames, username_warnings = normalize_collection(
        IdentifierKind.USERNAME,
        ["Demo_User", "demo_user"],
    )

    assert [item.normalized_value for item in emails] == [
        "User@example.com",
        "user@example.com",
    ]
    assert [item.normalized_value for item in usernames] == [
        "Demo_User",
        "demo_user",
    ]
    assert email_warnings == []
    assert username_warnings == []


def test_url_normalization_keeps_case_sensitive_components_and_fragment() -> None:
    result = normalize_identifier(
        IdentifierKind.URL,
        "Example.COM/Profile?tab=about#Section",
    )
    assert result.normalized_value == "https://example.com/Profile?tab=about#Section"
    assert result.comparison_key == "https://example.com/Profile?tab=about#Section"


def test_public_url_hostname_is_canonicalized_through_idna() -> None:
    result = normalize_identifier(
        IdentifierKind.URL,
        "https://BÜCHER.example/Profile",
    )
    assert result.normalized_value == "https://xn--bcher-kva.example/Profile"


@pytest.mark.parametrize(
    "value",
    [
        "ftp://example.com/profile",
        "file://example.com/etc/passwd",
        "gopher://example.com/resource",
        "https://localhost/profile",
        "https://intranet/profile",
        "https://person.internal/profile",
        "https://person.local/profile",
        "https://127.0.0.1/profile",
        "https://10.0.0.8/profile",
        "https://8.8.8.8/profile",
        "https://[::1]/profile",
        "https://[2606:4700:4700::1111]/profile",
        "https://@example.com/profile",
        "https://example.com/profile with space",
        "https://example.com/profile\nnext",
    ],
)
def test_public_url_seed_rejects_non_web_or_non_dns_destinations(value: str) -> None:
    with pytest.raises(InvalidIdentifier):
        normalize_identifier(IdentifierKind.URL, value)


def test_malformed_ipv6_url_is_reported_as_invalid_identifier() -> None:
    with pytest.raises(InvalidIdentifier, match="malformed"):
        normalize_identifier(IdentifierKind.URL, "https://[not-an-ipv6/profile")


def test_collection_deduplicates_only_on_safe_generic_equivalence() -> None:
    results, warnings = normalize_collection(
        IdentifierKind.EMAIL,
        ["A@Example.com", "A@example.com", "bad email"],
    )
    assert [item.normalized_value for item in results] == ["A@example.com"]
    assert len(warnings) == 1


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        (IdentifierKind.PHONE, "not-a-phone"),
        (IdentifierKind.EMAIL, "broken email"),
        (IdentifierKind.USERNAME, "@"),
        (IdentifierKind.URL, "https://"),
    ],
)
def test_malformed_identifiers_are_rejected(kind: IdentifierKind, value: str) -> None:
    with pytest.raises(InvalidIdentifier):
        normalize_identifier(kind, value)
