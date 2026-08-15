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


def test_email_and_username_normalization_is_deterministic() -> None:
    email = normalize_identifier(IdentifierKind.EMAIL, " Test@Example.COM ")
    username = normalize_identifier(IdentifierKind.USERNAME, " @Demo_User ")

    assert email.normalized_value == "test@example.com"
    assert email.comparison_key == "test@example.com"
    assert username.normalized_value == "Demo_User"
    assert username.comparison_key == "demo_user"


def test_url_normalization_drops_fragment_and_normalizes_host() -> None:
    result = normalize_identifier(
        IdentifierKind.URL,
        "Example.COM/Profile?tab=about#section",
    )
    assert result.normalized_value == "https://example.com/Profile?tab=about"
    assert result.comparison_key == "https://example.com/Profile?tab=about"


def test_collection_deduplicates_by_comparison_key() -> None:
    results, warnings = normalize_collection(
        IdentifierKind.EMAIL,
        ["A@Example.com", "a@example.com", "bad email"],
    )
    assert [item.normalized_value for item in results] == ["a@example.com"]
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
