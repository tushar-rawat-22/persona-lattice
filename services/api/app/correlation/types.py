# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class FactorKind(str, Enum):
    SAME_USERNAME = "same_username"
    EXACT_CONFIRMED_IDENTIFIER_OVERLAP = "exact_confirmed_identifier_overlap"
    INDEPENDENT_CROSS_LINK = "independent_cross_link"
    COMPATIBLE_PROFILE_METADATA = "compatible_profile_metadata"
    TEMPORAL_COMPATIBILITY = "temporal_compatibility"
    HARD_CONTRADICTION = "hard_contradiction"


class FactorStatus(str, Enum):
    APPLIED = "applied"
    APPLIED_UNKNOWN_FRESHNESS = "applied_unknown_freshness"
    NOT_APPLICABLE = "not_applicable"
    EXCLUDED_STALE = "excluded_stale"
    SUPPRESSED_SAME_INDEPENDENCE_GROUP = "suppressed_same_independence_group"


class CorrelationOutcome(str, Enum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    POSSIBLE_MATCH = "possible_match"
    STRONG_CANDIDATE = "strong_candidate"
    CONTRADICTED = "contradicted"


class CalibrationStatus(str, Enum):
    UNCALIBRATED = "uncalibrated"


@dataclass(frozen=True, slots=True)
class CorrelationFactorInput:
    kind: FactorKind
    observation_ids: tuple[UUID, ...] = ()
    identifier_ids: tuple[UUID, ...] = ()
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class CorrelationRequest:
    subject_id: UUID
    candidate_observation_id: UUID
    evaluated_at: datetime
    factors: tuple[CorrelationFactorInput, ...]


@dataclass(frozen=True, slots=True)
class CorrelationFactorResult:
    kind: FactorKind
    independence_group: str
    base_weight: int
    applied_weight: int
    status: FactorStatus
    observation_ids: tuple[str, ...]
    identifier_ids: tuple[str, ...]
    rationale: str
    veto: bool


@dataclass(frozen=True, slots=True)
class CorrelationResult:
    run_id: UUID
    policy_version: str
    subject_id: UUID
    candidate_observation_id: UUID
    evaluated_at: str
    outcome: CorrelationOutcome
    evidence_score: int
    calibration_status: CalibrationStatus
    positive_independence_groups: int
    factors: tuple[CorrelationFactorResult, ...]
    input_digest: str
    output_digest: str
    normalized_output: str
    is_identity_claim: bool = False
