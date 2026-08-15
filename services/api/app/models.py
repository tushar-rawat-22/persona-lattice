# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class Purpose(str, Enum):
    SELF_AUDIT = "self_audit"
    CONSENTED_DUE_DILIGENCE = "consented_due_diligence"
    PUBLIC_SOURCE_RESEARCH = "public_source_research"
    PROFESSIONAL_VERIFICATION = "professional_verification"

    EMPLOYMENT_DECISION = "employment_decision"
    HOUSING_DECISION = "housing_decision"
    CREDIT_DECISION = "credit_decision"
    INSURANCE_DECISION = "insurance_decision"


class FileHint(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    media_type: str | None = Field(default=None, max_length=120)
    size_bytes: int | None = Field(default=None, ge=0)


class CaseIntake(BaseModel):
    purpose: Purpose
    consent_acknowledged: bool = False

    full_name: str | None = Field(default=None, max_length=200)
    phones: list[str] = Field(default_factory=list, max_length=20)
    emails: list[str] = Field(default_factory=list, max_length=50)
    usernames: list[str] = Field(default_factory=list, max_length=100)
    urls: list[str] = Field(default_factory=list, max_length=100)
    organizations: list[str] = Field(default_factory=list, max_length=50)
    notes: str | None = Field(default=None, max_length=20_000)
    files: list[FileHint] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def at_least_one_signal(self) -> "CaseIntake":
        has_signal = any(
            [
                bool(self.full_name),
                bool(self.phones),
                bool(self.emails),
                bool(self.usernames),
                bool(self.urls),
                bool(self.organizations),
                bool(self.notes),
                bool(self.files),
            ]
        )
        if not has_signal:
            raise ValueError("Provide at least one identifier, note, organization, URL, or file.")
        return self


class ProviderPlan(BaseModel):
    provider: str
    capability: str
    status: str
    contact_risk: str
    reason: str


class IntakePreview(BaseModel):
    case_id: UUID
    status: str
    purpose: Purpose
    normalized: dict[str, Any]
    provider_plan: list[ProviderPlan]
    warnings: list[str]
