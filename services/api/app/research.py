# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit
from uuid import uuid4

from phonenumbers import carrier, geocoder, timezone

from .evidence import IdentifierKind, normalize_identifier
from .models import Purpose
from .providers.base import ProviderObservationData, ProviderQuery
from .providers.contracts import ExecutionRequest
from .providers.policy import authorize_execution
from .providers.rate_limit import RateBudget
from .providers.sherlock import SherlockProvider


class ResearchKind(StrEnum):
    USERNAME = "username"
    PHONE = "phone"
    EMAIL = "email"
    URL = "url"


@dataclass(frozen=True, slots=True)
class QuickObservation:
    source: str
    source_locator: str
    summary: str
    details: dict[str, object]


@dataclass(frozen=True, slots=True)
class QuickResearchReport:
    kind: ResearchKind
    normalized_value: str
    observations: tuple[QuickObservation, ...]
    warnings: tuple[str, ...] = ()


_SHERLOCK_BUDGET = RateBudget(limit=6, window_seconds=60.0)


def _observation_from_provider(item: ProviderObservationData) -> QuickObservation:
    state = str(item.payload.get("account_state", "unknown"))
    site = str(item.payload.get("site", "public account"))
    return QuickObservation(
        source="sherlock",
        source_locator=item.source_locator,
        summary=f"{site}: {state}",
        details=dict(item.payload),
    )


async def _research_username(
    normalized_value: str,
    *,
    purpose: Purpose,
    consent_acknowledged: bool,
    provider: SherlockProvider | None = None,
) -> QuickResearchReport:
    adapter = provider or SherlockProvider()
    subject_id = uuid4()
    identifier_id = uuid4()
    authorize_execution(
        adapter.descriptor,
        ExecutionRequest(
            provider_name=adapter.descriptor.name,
            subject_id=subject_id,
            identifier_id=identifier_id,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
        ),
    )
    _SHERLOCK_BUDGET.consume()
    result = await adapter.execute(
        ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.USERNAME.value,
            identifier_value=normalized_value,
        ),
        None,
    )
    return QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value=normalized_value,
        observations=tuple(_observation_from_provider(item) for item in result.observations),
    )


def _research_phone(normalized_value: str) -> QuickResearchReport:
    import phonenumbers

    parsed = phonenumbers.parse(normalized_value, None)
    region = geocoder.description_for_number(parsed, "en") or None
    network = carrier.name_for_number(parsed, "en") or None
    timezones = tuple(timezone.time_zones_for_number(parsed))
    details: dict[str, object] = {
        "country_code": parsed.country_code,
        "national_number": str(parsed.national_number),
        "possible": phonenumbers.is_possible_number(parsed),
        "valid": phonenumbers.is_valid_number(parsed),
        "region": region,
        "carrier": network,
        "timezones": timezones,
        "personal_identity_claim": False,
    }
    return QuickResearchReport(
        kind=ResearchKind.PHONE,
        normalized_value=normalized_value,
        observations=(
            QuickObservation(
                source="libphonenumber_metadata",
                source_locator="local://libphonenumber",
                summary="Numbering-plan metadata; not subscriber identity.",
                details=details,
            ),
        ),
    )


def _research_email(normalized_value: str) -> QuickResearchReport:
    local_part, domain = normalized_value.rsplit("@", 1)
    return QuickResearchReport(
        kind=ResearchKind.EMAIL,
        normalized_value=normalized_value,
        observations=(
            QuickObservation(
                source="local_normalization",
                source_locator=f"domain://{domain.lower()}",
                summary="Normalized email and domain extracted locally.",
                details={
                    "domain": domain.lower(),
                    "local_part_length": len(local_part),
                    "personal_identity_claim": False,
                },
            ),
        ),
        warnings=(
            "No external email-enrichment provider is approved yet; this report does not infer an owner.",
        ),
    )


def _research_url(normalized_value: str) -> QuickResearchReport:
    parts = urlsplit(normalized_value)
    return QuickResearchReport(
        kind=ResearchKind.URL,
        normalized_value=normalized_value,
        observations=(
            QuickObservation(
                source="local_normalization",
                source_locator=normalized_value,
                summary="Canonical public URL metadata extracted locally.",
                details={
                    "scheme": parts.scheme,
                    "hostname": parts.hostname,
                    "path": parts.path,
                    "personal_identity_claim": False,
                },
            ),
        ),
    )


async def run_quick_research(
    *,
    kind: ResearchKind,
    value: str,
    purpose: Purpose,
    consent_acknowledged: bool,
    sherlock_provider: SherlockProvider | None = None,
) -> QuickResearchReport:
    identifier_kind = IdentifierKind(kind.value)
    normalized = normalize_identifier(identifier_kind, value)

    if kind is ResearchKind.USERNAME:
        return await _research_username(
            normalized.normalized_value,
            purpose=purpose,
            consent_acknowledged=consent_acknowledged,
            provider=sherlock_provider,
        )
    if kind is ResearchKind.PHONE:
        return _research_phone(normalized.normalized_value)
    if kind is ResearchKind.EMAIL:
        return _research_email(normalized.normalized_value)
    if kind is ResearchKind.URL:
        return _research_url(normalized.normalized_value)
    raise ValueError("Unsupported research kind.")
