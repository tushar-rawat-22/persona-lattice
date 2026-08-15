# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

import phonenumbers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


def normalize_phone(raw: str) -> tuple[str, str | None]:
    try:
        parsed = phonenumbers.parse(raw, None)
        if not phonenumbers.is_possible_number(parsed):
            return raw.strip(), "Phone is not recognized as a possible number."
        normalized = phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.E164,
        )
        return normalized, None
    except phonenumbers.NumberParseException:
        return raw.strip(), "Phone could not be normalized."


@app.post("/v1/intake/preview", response_model=IntakePreview)
def preview_intake(payload: CaseIntake) -> IntakePreview:
    enforce_purpose(payload.purpose, payload.consent_acknowledged)

    warnings: list[str] = []
    phones: list[str] = []

    for raw in payload.phones:
        normalized, warning = normalize_phone(raw)
        phones.append(normalized)
        if warning:
            warnings.append(f"{raw}: {warning}")

    normalized = {
        "full_name": payload.full_name.strip() if payload.full_name else None,
        "phones": sorted(set(phones)),
        "emails": sorted({value.strip().lower() for value in payload.emails if value.strip()}),
        "usernames": sorted({value.strip().lstrip("@") for value in payload.usernames if value.strip()}),
        "urls": sorted({value.strip() for value in payload.urls if value.strip()}),
        "organizations": sorted(
            {value.strip() for value in payload.organizations if value.strip()}
        ),
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
