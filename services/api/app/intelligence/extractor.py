# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass

from ..evidence.normalization import InvalidIdentifier
from .contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadExtractionResult,
    LeadKind,
    LeadReason,
    canonicalize_lead,
)


@dataclass(frozen=True, slots=True)
class _FieldRule:
    kind: LeadKind
    reason: LeadReason
    disposition: LeadDisposition


# This is intentionally an exact allowlist. Arbitrary provider payload keys must
# never become recursive lookups merely because they contain string-like data.
_FIELD_RULES: dict[str, _FieldRule] = {
    "email": _FieldRule(LeadKind.EMAIL, LeadReason.PUBLIC_EMAIL, LeadDisposition.AUTO_PIVOT),
    "public_email": _FieldRule(LeadKind.EMAIL, LeadReason.PUBLIC_EMAIL, LeadDisposition.AUTO_PIVOT),
    "username": _FieldRule(LeadKind.USERNAME, LeadReason.PUBLIC_USERNAME, LeadDisposition.AUTO_PIVOT),
    "login": _FieldRule(LeadKind.USERNAME, LeadReason.PUBLIC_USERNAME, LeadDisposition.AUTO_PIVOT),
    "handle": _FieldRule(LeadKind.USERNAME, LeadReason.PUBLIC_USERNAME, LeadDisposition.AUTO_PIVOT),
    "twitter_username": _FieldRule(LeadKind.USERNAME, LeadReason.PUBLIC_USERNAME, LeadDisposition.AUTO_PIVOT),
    "twitter": _FieldRule(LeadKind.USERNAME, LeadReason.PUBLIC_USERNAME, LeadDisposition.AUTO_PIVOT),
    "blog": _FieldRule(LeadKind.URL, LeadReason.PUBLIC_URL, LeadDisposition.AUTO_PIVOT),
    "website_url": _FieldRule(LeadKind.URL, LeadReason.PUBLIC_URL, LeadDisposition.AUTO_PIVOT),
    "profile_url": _FieldRule(LeadKind.URL, LeadReason.PUBLIC_URL, LeadDisposition.AUTO_PIVOT),
    "phone": _FieldRule(LeadKind.PHONE, LeadReason.PUBLIC_PHONE, LeadDisposition.REVIEW_REQUIRED),
    "phone_number": _FieldRule(LeadKind.PHONE, LeadReason.PUBLIC_PHONE, LeadDisposition.REVIEW_REQUIRED),
    "public_phone": _FieldRule(LeadKind.PHONE, LeadReason.PUBLIC_PHONE, LeadDisposition.REVIEW_REQUIRED),
    "domain": _FieldRule(LeadKind.DOMAIN, LeadReason.PUBLIC_DOMAIN, LeadDisposition.DISPLAY_ONLY),
    "name": _FieldRule(LeadKind.NAME, LeadReason.PUBLIC_NAME, LeadDisposition.DISPLAY_ONLY),
    "full_name": _FieldRule(LeadKind.NAME, LeadReason.PUBLIC_NAME, LeadDisposition.DISPLAY_ONLY),
    "display_name": _FieldRule(LeadKind.NAME, LeadReason.PUBLIC_NAME, LeadDisposition.DISPLAY_ONLY),
    "company": _FieldRule(
        LeadKind.ORGANIZATION,
        LeadReason.PUBLIC_ORGANIZATION,
        LeadDisposition.DISPLAY_ONLY,
    ),
    "organization": _FieldRule(
        LeadKind.ORGANIZATION,
        LeadReason.PUBLIC_ORGANIZATION,
        LeadDisposition.DISPLAY_ONLY,
    ),
    "employer": _FieldRule(
        LeadKind.ORGANIZATION,
        LeadReason.PUBLIC_ORGANIZATION,
        LeadDisposition.DISPLAY_ONLY,
    ),
    "location": _FieldRule(
        LeadKind.LOCATION,
        LeadReason.PUBLIC_LOCATION,
        LeadDisposition.DISPLAY_ONLY,
    ),
    "region": _FieldRule(
        LeadKind.LOCATION,
        LeadReason.PUBLIC_LOCATION,
        LeadDisposition.DISPLAY_ONLY,
    ),
}


# Values behind these keys are never copied into the lead graph. The field name
# may be reported for audit/debugging so a future adapter can be corrected without
# retaining or autonomously propagating highly sensitive material.
_BLOCKED_FIELD_NAMES = {
    "aadhaar",
    "aadhaar_number",
    "aadhar",
    "aadhar_number",
    "government_id",
    "national_id",
    "passport_number",
    "ssn",
    "password",
    "otp",
    "access_token",
    "refresh_token",
    "auth_token",
    "device_ip",
    "last_ip",
    "personal_ip",
}


def _text(value: object) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def extract_observation_leads(
    *,
    details: dict[str, object],
    source: str,
    source_locator: str,
) -> LeadExtractionResult:
    """Extract deterministic lead candidates from one reviewed observation.

    Only exact allowlisted fields are considered. Blocked fields are recorded by
    name only, and malformed values are ignored rather than guessed into shape.
    """

    candidates: dict[str, LeadCandidate] = {}
    blocked = sorted(name for name in details if name in _BLOCKED_FIELD_NAMES)

    for field_name, rule in _FIELD_RULES.items():
        value = _text(details.get(field_name))
        if value is None:
            continue
        try:
            normalized_value, comparison_key = canonicalize_lead(rule.kind, value)
        except InvalidIdentifier:
            continue

        candidate = LeadCandidate(
            kind=rule.kind,
            value=normalized_value,
            comparison_key=comparison_key,
            reason=rule.reason,
            disposition=rule.disposition,
            source=source,
            source_locator=source_locator,
            field_name=field_name,
        )
        candidates.setdefault(candidate.key, candidate)

    ordered = tuple(
        sorted(
            candidates.values(),
            key=lambda item: (
                item.disposition.value,
                item.kind.value,
                item.comparison_key,
                item.field_name,
            ),
        )
    )
    return LeadExtractionResult(
        candidates=ordered,
        blocked_field_names=tuple(blocked),
    )
