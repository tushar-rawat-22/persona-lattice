# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence import LeadDisposition, LeadKind, extract_observation_leads


def _extract(details: dict[str, object]):
    return extract_observation_leads(
        details=details,
        source="synthetic_public_source",
        source_locator="https://example.test/profile",
    )


def test_lead_extractor_only_auto_pivots_reviewed_public_identifier_fields() -> None:
    result = _extract(
        {
            "public_email": "Person@Example.TEST",
            "handle": "CaseSensitiveHandle",
            "website_url": "example.test/profile",
            "phone_number": "+919876543210",
            "company": "Example Corp",
            "location": "Bengaluru",
        }
    )

    by_kind = {candidate.kind: candidate for candidate in result.candidates}

    assert by_kind[LeadKind.EMAIL].value == "Person@example.test"
    assert by_kind[LeadKind.EMAIL].disposition is LeadDisposition.AUTO_PIVOT
    assert by_kind[LeadKind.USERNAME].value == "CaseSensitiveHandle"
    assert by_kind[LeadKind.USERNAME].disposition is LeadDisposition.AUTO_PIVOT
    assert by_kind[LeadKind.URL].value == "https://example.test/profile"
    assert by_kind[LeadKind.URL].disposition is LeadDisposition.AUTO_PIVOT
    assert by_kind[LeadKind.PHONE].disposition is LeadDisposition.REVIEW_REQUIRED
    assert by_kind[LeadKind.ORGANIZATION].disposition is LeadDisposition.DISPLAY_ONLY
    assert by_kind[LeadKind.LOCATION].disposition is LeadDisposition.DISPLAY_ONLY


def test_lead_extractor_does_not_turn_arbitrary_payload_keys_into_queries() -> None:
    result = _extract(
        {
            "linkedin": "person-name",
            "discord": "person#0001",
            "favorite_game": "example-game",
            "unreviewed_emailish_field": "other@example.test",
        }
    )

    assert result.candidates == ()
    assert result.blocked_field_names == ()


def test_lead_extractor_blocks_highly_sensitive_fields_without_copying_values() -> None:
    result = _extract(
        {
            "aadhaar_number": "1111-2222-3333",
            "password": "do-not-retain",
            "ip": "203.0.113.99",
            "device_ip": "198.51.100.42",
            "public_email": "safe@example.test",
        }
    )

    assert result.blocked_field_names == (
        "aadhaar_number",
        "device_ip",
        "ip",
        "password",
    )
    serialized = repr(result)
    assert "1111-2222-3333" not in serialized
    assert "do-not-retain" not in serialized
    assert "203.0.113.99" not in serialized
    assert "198.51.100.42" not in serialized
    assert any(candidate.value == "safe@example.test" for candidate in result.candidates)


def test_generic_lead_keys_preserve_m1_username_and_email_local_part_case() -> None:
    first = _extract({"username": "CaseHandle", "email": "Person@example.test"})
    second = _extract({"username": "casehandle", "email": "person@example.test"})

    first_keys = {candidate.key for candidate in first.candidates}
    second_keys = {candidate.key for candidate in second.candidates}

    assert "username:CaseHandle" in first_keys
    assert "username:casehandle" in second_keys
    assert "email:Person@example.test" in first_keys
    assert "email:person@example.test" in second_keys
    assert first_keys != second_keys
