# SPDX-License-Identifier: Apache-2.0
from app.evidence import IdentifierKind, normalize_identifier
from app.providers import REDACTED_SECRET, sanitize_provider_log


def test_provider_log_redacts_phone_email_and_known_secret() -> None:
    email = normalize_identifier(IdentifierKind.EMAIL, "person@example.test")
    phone = normalize_identifier(IdentifierKind.PHONE, "+1 202 555 0123")
    secret = "sk-synthetic-super-secret"

    message = (
        "provider failed for person@example.test / +1 202-555-0123 "
        f"api_key={secret}"
    )
    redacted = sanitize_provider_log(
        message,
        identifiers=[email, phone],
        secrets=[secret],
    )

    assert "person@example.test" not in redacted
    assert "202-555" not in redacted
    assert secret not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert REDACTED_SECRET in redacted
