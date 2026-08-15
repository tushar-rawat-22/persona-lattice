# SPDX-License-Identifier: Apache-2.0
from app.evidence import IdentifierKind, normalize_identifier, redact_text


def test_redaction_removes_common_phone_email_and_username_forms() -> None:
    identifiers = [
        normalize_identifier(IdentifierKind.PHONE, "+91 98765 43210"),
        normalize_identifier(IdentifierKind.EMAIL, "person@example.com"),
        normalize_identifier(IdentifierKind.USERNAME, "@Some.User"),
    ]

    text = (
        "Call +91 98765 43210 or 98765 43210. "
        "The account email is PERSON@EXAMPLE.COM. "
        "Username Some.User was queried."
    )

    redacted = redact_text(text, identifiers)

    assert "+91 98765 43210" not in redacted
    assert "98765 43210" not in redacted
    assert "person@example.com" not in redacted.lower()
    assert "Some.User" not in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_USERNAME]" in redacted


def test_username_redaction_does_not_replace_substrings_inside_another_handle() -> None:
    identifier = normalize_identifier(IdentifierKind.USERNAME, "ann")
    redacted = redact_text("ann and joann-dev are different handles", [identifier])

    assert redacted.startswith("[REDACTED_USERNAME]")
    assert "joann-dev" in redacted
