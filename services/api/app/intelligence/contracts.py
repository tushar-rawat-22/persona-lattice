# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..evidence import IdentifierKind, normalize_identifier
from ..evidence.normalization import InvalidIdentifier


class LeadKind(StrEnum):
    """Kinds of clues that can exist in the recursive evidence graph.

    Only a subset are executable research seeds. Contextual attributes are
    represented so the UI/report can explain them without automatically turning
    every piece of personal data into another external lookup.
    """

    USERNAME = "username"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    DOMAIN = "domain"
    NAME = "name"
    ORGANIZATION = "organization"
    LOCATION = "location"


class LeadDisposition(StrEnum):
    AUTO_PIVOT = "auto_pivot"
    REVIEW_REQUIRED = "review_required"
    DISPLAY_ONLY = "display_only"
    BLOCKED = "blocked"


class LeadReason(StrEnum):
    PUBLIC_EMAIL = "public_email"
    PUBLIC_USERNAME = "public_username"
    PUBLIC_URL = "public_url"
    PUBLIC_PHONE = "public_phone"
    PUBLIC_DOMAIN = "public_domain"
    PUBLIC_NAME = "public_name"
    PUBLIC_ORGANIZATION = "public_organization"
    PUBLIC_LOCATION = "public_location"


_IDENTIFIER_KIND_BY_LEAD_KIND = {
    LeadKind.USERNAME: IdentifierKind.USERNAME,
    LeadKind.EMAIL: IdentifierKind.EMAIL,
    LeadKind.PHONE: IdentifierKind.PHONE,
    LeadKind.URL: IdentifierKind.URL,
    LeadKind.NAME: IdentifierKind.NAME,
    LeadKind.ORGANIZATION: IdentifierKind.ORGANIZATION,
}


def _compact(value: str) -> str:
    return " ".join(value.split())


def canonicalize_lead(kind: LeadKind, value: str) -> tuple[str, str]:
    """Return a display value and deterministic comparison key for a lead.

    Existing M1 normalization is reused for identifiers so the recursive graph
    cannot quietly invent a second, incompatible identity-normalization policy.
    """

    if kind in _IDENTIFIER_KIND_BY_LEAD_KIND:
        normalized = normalize_identifier(_IDENTIFIER_KIND_BY_LEAD_KIND[kind], value)
        return normalized.normalized_value, normalized.comparison_key

    compact = _compact(value)
    if not compact:
        raise InvalidIdentifier(f"{kind.value} is empty.")

    if kind is LeadKind.DOMAIN:
        candidate = compact.lower().rstrip(".")
        if not candidate or "." not in candidate or any(character.isspace() for character in candidate):
            raise InvalidIdentifier("Domain is malformed.")
        return candidate, candidate

    if kind is LeadKind.LOCATION:
        return compact, compact.casefold()

    raise InvalidIdentifier(f"Unsupported lead kind: {kind!r}")


@dataclass(frozen=True, slots=True)
class LeadCandidate:
    kind: LeadKind
    value: str
    comparison_key: str
    reason: LeadReason
    disposition: LeadDisposition
    source: str
    source_locator: str
    field_name: str

    @property
    def key(self) -> str:
        return f"{self.kind.value}:{self.comparison_key}"


@dataclass(frozen=True, slots=True)
class LeadExtractionResult:
    candidates: tuple[LeadCandidate, ...]
    blocked_field_names: tuple[str, ...] = ()
