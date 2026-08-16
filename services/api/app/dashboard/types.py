# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.correlation import (
    CalibrationStatus,
    CorrelationOutcome,
    FactorKind,
    FactorStatus,
)
from app.evidence import (
    ClaimOrigin,
    EvidenceRelation,
    FreshnessState,
    IdentifierKind,
    ObservationSourceKind,
)


class ReadModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class IdentifierView(ReadModel):
    id: UUID
    kind: IdentifierKind
    value: str = Field(max_length=2048)


class ProvenanceView(ReadModel):
    source_kind: ObservationSourceKind
    source_name: str = Field(max_length=120)
    source_locator: str = Field(max_length=2048)


class ObservationView(ReadModel):
    id: UUID
    identifier_id: UUID | None
    provenance: ProvenanceView
    retrieved_at: datetime
    observed_at: datetime | None
    expires_at: datetime | None
    freshness: FreshnessState
    summary: str = Field(max_length=180)
    account_candidate: bool
    identity_claim: bool | None
    candidate_observation_id: UUID | None


class EvidenceLinkView(ReadModel):
    observation_id: UUID
    relation: EvidenceRelation
    rationale: str | None = Field(default=None, max_length=500)


class ClaimView(ReadModel):
    id: UUID
    statement: str = Field(max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)
    origin: ClaimOrigin
    evidence_links: tuple[EvidenceLinkView, ...]


class CorrelationFactorView(ReadModel):
    kind: FactorKind
    independence_group: str = Field(max_length=120)
    base_weight: int
    applied_weight: int
    status: FactorStatus
    observation_ids: tuple[UUID, ...]
    identifier_ids: tuple[UUID, ...]
    rationale: str = Field(max_length=500)
    veto: bool


class CorrelationView(ReadModel):
    run_id: UUID
    policy_version: str = Field(max_length=80)
    candidate_observation_id: UUID
    evaluated_at: datetime
    outcome: CorrelationOutcome
    evidence_score: int = Field(ge=0, le=100)
    calibration_status: CalibrationStatus
    positive_independence_groups: int = Field(ge=0)
    factors: tuple[CorrelationFactorView, ...]
    is_identity_claim: bool


class AccountCandidateView(ReadModel):
    observation_id: UUID
    identifier_id: UUID
    source_name: str = Field(max_length=120)
    site: str | None = Field(default=None, max_length=120)
    profile_url: str = Field(max_length=2048)
    correlation: CorrelationView | None


class CaseReadModel(ReadModel):
    schema_version: str = Field(max_length=80)
    generated_at: datetime
    subject_id: UUID
    display_name: str | None = Field(default=None, max_length=200)
    identifiers: tuple[IdentifierView, ...]
    observations: tuple[ObservationView, ...]
    claims: tuple[ClaimView, ...]
    account_candidates: tuple[AccountCandidateView, ...]
