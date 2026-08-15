# SPDX-License-Identifier: Apache-2.0
from app.evidence import IdentifierKind, normalize_identifier, redact_text


def test_redaction_removes_common_phone_and_email_forms() -> None:
    identifiers = [
        normalize_identifier(IdentifierKind.PHONE, "+91 98765 43210"),
        normalize_identifier(IdentifierKind.EMAIL, "person@example.com"),
    ]

    text = (
        "Call +91 98765 43210 or 98765 43210. "
        "The account email is PERSON@EXAMPLE.COM."
    )

    redacted = redact_text(text, identifiers)

    assert "+91 98765 43210" not in redacted
    assert "98765 43210" not in redacted
    assert "person@example.com" not in redacted.lower()
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_EMAIL]" in redacted
