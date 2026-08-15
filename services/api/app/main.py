# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .evidence import IdentifierKind, InvalidIdentifier, normalize_collection, normalize_identifier
from .models import CaseIntake, IntakePreview, ProviderPlan
from .policy import enforce_purpose
from .providers.registry import PROVIDERS

app = FastAPI(
    title="PersonaLattice API",
    version="0.0.1",
    description="Evidence-first identity intelligence API bootstrap.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "personalattice-api"}


def _normalize_scalar(kind: IdentifierKind, raw: str | None) -> tuple[str | None, list[str]]:
    if raw is None:
        return None, []

    try:
        normalized = normalize_identifier(kind, raw)
    except InvalidIdentifier as exc:
        return None, [f"{raw}: {exc}"]

    return normalized.normalized_value, []


def _normalize_values(kind: IdentifierKind, values: list[str]) -> tuple[list[str], list[str]]:
    normalized, warnings = normalize_collection(kind, values)
    return [item.normalized_value for item in normalized], warnings


@app.post("/v1/intake/preview", response_model=IntakePreview)
def preview_intake(payload: CaseIntake) -> IntakePreview:
    enforce_purpose(payload.purpose, payload.consent_acknowledged)

    warnings: list[str] = []

    full_name, scalar_warnings = _normalize_scalar(
        IdentifierKind.NAME,
        payload.full_name,
    )
    warnings.extend(scalar_warnings)

    phones, phone_warnings = _normalize_values(IdentifierKind.PHONE, payload.phones)
    warnings.extend(phone_warnings)

    emails, email_warnings = _normalize_values(IdentifierKind.EMAIL, payload.emails)
    warnings.extend(email_warnings)

    usernames, username_warnings = _normalize_values(
        IdentifierKind.USERNAME,
        payload.usernames,
    )
    warnings.extend(username_warnings)

    urls, url_warnings = _normalize_values(IdentifierKind.URL, payload.urls)
    warnings.extend(url_warnings)

    organizations, organization_warnings = _normalize_values(
        IdentifierKind.ORGANIZATION,
        payload.organizations,
    )
    warnings.extend(organization_warnings)

    normalized = {
        "full_name": full_name,
        "phones": phones,
        "emails": emails,
        "usernames": usernames,
        "urls": urls,
        "organizations": organizations,
        "file_count": len(payload.files),
        "note_present": bool(payload.notes),
    }

    plans = [
        ProviderPlan(
            provider=item.name,
            capability=item.capability,
            status=item.status,
            contact_risk=item.contact_risk.value,
            reason=item.reason,
        )
        for item in PROVIDERS
    ]

    return IntakePreview(
        case_id=uuid4(),
        status="planned_only",
        purpose=payload.purpose,
        normalized=normalized,
        provider_plan=plans,
        warnings=warnings,
    )
