# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.evidence.models import Identifier, Observation
from app.evidence.types import FreshnessState, IdentifierKind

from .models import CorrelationFactorRecord, CorrelationRun
from .policy import (
    FACTOR_WEIGHTS,
    MIN_STRONG_INDEPENDENCE_GROUPS,
    M5_POLICY_VERSION,
    POSSIBLE_MATCH_THRESHOLD,
    STRONG_CANDIDATE_THRESHOLD,
    STRONG_FACTOR_KINDS,
    VETO_FACTOR_KINDS,
)
from .types import (
    CalibrationStatus,
    CorrelationFactorInput,
    CorrelationFactorResult,
    CorrelationOutcome,
    CorrelationRequest,
    CorrelationResult,
    FactorKind,
    FactorStatus,
)

MAX_GROUP_CHARS = 120
MAX_RATIONALE_CHARS = 500


class CorrelationValidationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _PreparedFactor:
    kind: FactorKind
    independence_group: str
    observation_ids: tuple[str, ...]
    identifier_ids: tuple[str, ...]
    rationale: str
    base_weight: int
    freshness_status: FactorStatus


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise CorrelationValidationError("Correlation evaluated_at must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_group(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > MAX_GROUP_CHARS:
        raise CorrelationValidationError("Factor independence_group is missing or too long.")
    return normalized


def _normalize_rationale(value: str) -> str:
    normalized = " ".join(value.split())
    if len(normalized) > MAX_RATIONALE_CHARS:
        raise CorrelationValidationError("Factor rationale exceeds the configured limit.")
    return normalized


def _factor_sort_key(factor: _PreparedFactor) -> tuple[object, ...]:
    return (
        factor.kind.value,
        factor.independence_group,
        factor.observation_ids,
        factor.identifier_ids,
        factor.rationale,
    )


class CorrelationEngine:
    """Deterministic M5 evidence-strength engine; it never creates identity claims."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def correlate(self, request: CorrelationRequest) -> CorrelationResult:
        evaluated_at = _as_utc(request.evaluated_at)
        candidate = self._load_candidate(request)
        prepared = tuple(
            sorted(
                (self._prepare_factor(request.subject_id, factor, evaluated_at) for factor in request.factors),
                key=_factor_sort_key,
            )
        )
        if not prepared:
            raise CorrelationValidationError("At least one evidence factor is required.")

        input_payload = {
            "candidate_observation_id": str(candidate.id),
            "evaluated_at": _iso_utc(evaluated_at),
            "factors": [
                {
                    "identifier_ids": list(factor.identifier_ids),
                    "independence_group": factor.independence_group,
                    "kind": factor.kind.value,
                    "observation_ids": list(factor.observation_ids),
                    "rationale": factor.rationale,
                }
                for factor in prepared
            ],
            "policy_version": M5_POLICY_VERSION,
            "subject_id": str(request.subject_id),
        }
        input_digest = _sha256(_canonical_json(input_payload))
        existing = self.session.scalar(
            select(CorrelationRun).where(
                CorrelationRun.subject_id == request.subject_id,
                CorrelationRun.candidate_observation_id == candidate.id,
                CorrelationRun.policy_version == M5_POLICY_VERSION,
                CorrelationRun.input_digest == input_digest,
            )
        )
        if existing is not None:
            return self._result_from_run(existing)

        factor_results = self._apply_policy(prepared)
        veto = any(result.veto and result.applied_weight < 0 for result in factor_results)
        positive_groups = {
            result.independence_group for result in factor_results if result.applied_weight > 0
        }
        raw_score = sum(result.applied_weight for result in factor_results)
        evidence_score = 0 if veto else max(0, min(100, raw_score))
        has_strong_factor = any(
            result.kind in STRONG_FACTOR_KINDS and result.applied_weight > 0
            for result in factor_results
        )

        if veto:
            outcome = CorrelationOutcome.CONTRADICTED
        elif (
            evidence_score >= STRONG_CANDIDATE_THRESHOLD
            and len(positive_groups) >= MIN_STRONG_INDEPENDENCE_GROUPS
            and has_strong_factor
        ):
            outcome = CorrelationOutcome.STRONG_CANDIDATE
        elif evidence_score >= POSSIBLE_MATCH_THRESHOLD:
            outcome = CorrelationOutcome.POSSIBLE_MATCH
        else:
            outcome = CorrelationOutcome.INSUFFICIENT_EVIDENCE

        output_payload = {
            "calibration_status": CalibrationStatus.UNCALIBRATED.value,
            "candidate_observation_id": str(candidate.id),
            "evaluated_at": _iso_utc(evaluated_at),
            "evidence_score": evidence_score,
            "factors": [self._factor_result_payload(result) for result in factor_results],
            "is_identity_claim": False,
            "outcome": outcome.value,
            "policy_version": M5_POLICY_VERSION,
            "positive_independence_groups": len(positive_groups),
            "subject_id": str(request.subject_id),
        }
        normalized_output = _canonical_json(output_payload)
        output_digest = _sha256(normalized_output)

        run = CorrelationRun(
            subject_id=request.subject_id,
            candidate_observation_id=candidate.id,
            policy_version=M5_POLICY_VERSION,
            evaluated_at=evaluated_at,
            input_digest=input_digest,
            output_digest=output_digest,
            normalized_output=normalized_output,
        )
        self.session.add(run)
        self.session.flush()
        for ordinal, result in enumerate(factor_results):
            self.session.add(
                CorrelationFactorRecord(
                    run_id=run.id,
                    ordinal=ordinal,
                    kind=result.kind.value,
                    independence_group=result.independence_group,
                    base_weight=result.base_weight,
                    applied_weight=result.applied_weight,
                    status=result.status.value,
                    veto=result.veto,
                    observation_ids=list(result.observation_ids),
                    identifier_ids=list(result.identifier_ids),
                    rationale=result.rationale,
                )
            )
        self.session.flush()
        return self._result_from_run(run)

    def _load_candidate(self, request: CorrelationRequest) -> Observation:
        candidate = self.session.get(Observation, request.candidate_observation_id)
        if candidate is None or candidate.subject_id != request.subject_id:
            raise CorrelationValidationError("Candidate observation does not belong to the subject.")
        if candidate.payload.get("account_candidate") is not True:
            raise CorrelationValidationError("Correlation candidate is not an account candidate.")
        if candidate.payload.get("identity_claim") is not False:
            raise CorrelationValidationError("Correlation candidate must explicitly remain non-identity evidence.")
        if candidate.identifier_id is None:
            raise CorrelationValidationError("Account candidate must retain its source identifier.")
        identifier = self.session.get(Identifier, candidate.identifier_id)
        if identifier is None or identifier.kind is not IdentifierKind.USERNAME:
            raise CorrelationValidationError("M5 account candidates must originate from usernames.")
        return candidate

    def _prepare_factor(
        self,
        subject_id: UUID,
        factor: CorrelationFactorInput,
        evaluated_at: datetime,
    ) -> _PreparedFactor:
        try:
            kind = FactorKind(factor.kind)
        except ValueError as exc:
            raise CorrelationValidationError("Unknown correlation factor kind.") from exc

        group = _normalize_group(factor.independence_group)
        rationale = _normalize_rationale(factor.rationale)
        observation_ids = tuple(sorted({str(value) for value in factor.observation_ids}))
        identifier_ids = tuple(sorted({str(value) for value in factor.identifier_ids}))
        if not observation_ids and not identifier_ids:
            raise CorrelationValidationError("A factor must reference stored evidence.")

        observations: list[Observation] = []
        for observation_id in observation_ids:
            observation = self.session.get(Observation, UUID(observation_id))
            if observation is None or observation.subject_id != subject_id:
                raise CorrelationValidationError("Factor observation does not belong to the subject.")
            observations.append(observation)

        identifiers: list[Identifier] = []
        for identifier_id in identifier_ids:
            identifier = self.session.get(Identifier, UUID(identifier_id))
            if identifier is None or identifier.subject_id != subject_id:
                raise CorrelationValidationError("Factor identifier does not belong to the subject.")
            identifiers.append(identifier)

        if kind is FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP:
            if not identifiers:
                raise CorrelationValidationError(
                    "Exact confirmed identifier overlap requires a stored identifier."
                )
            if any(identifier.kind is IdentifierKind.USERNAME for identifier in identifiers):
                raise CorrelationValidationError(
                    "Username reuse cannot be promoted to exact confirmed identifier overlap."
                )

        if kind is FactorKind.SAME_USERNAME and not observations:
            raise CorrelationValidationError("Same-username evidence requires an observation.")
        if kind is FactorKind.HARD_CONTRADICTION and not observations:
            raise CorrelationValidationError("Hard contradiction requires source observation evidence.")

        freshness = FactorStatus.NOT_APPLICABLE
        if observations:
            states = [observation.freshness(evaluated_at) for observation in observations]
            if FreshnessState.STALE in states:
                freshness = FactorStatus.EXCLUDED_STALE
            elif FreshnessState.UNKNOWN in states:
                freshness = FactorStatus.APPLIED_UNKNOWN_FRESHNESS
            else:
                freshness = FactorStatus.APPLIED

        return _PreparedFactor(
            kind=kind,
            independence_group=group,
            observation_ids=observation_ids,
            identifier_ids=identifier_ids,
            rationale=rationale,
            base_weight=FACTOR_WEIGHTS[kind],
            freshness_status=freshness,
        )

    def _apply_policy(
        self,
        prepared: tuple[_PreparedFactor, ...],
    ) -> tuple[CorrelationFactorResult, ...]:
        positive_winner_by_group: dict[str, int] = {}
        for index, factor in enumerate(prepared):
            if factor.base_weight <= 0 or factor.freshness_status is FactorStatus.EXCLUDED_STALE:
                continue
            current = positive_winner_by_group.get(factor.independence_group)
            if current is None:
                positive_winner_by_group[factor.independence_group] = index
                continue
            winner = prepared[current]
            candidate_key = (-factor.base_weight, factor.kind.value, factor.observation_ids, factor.identifier_ids)
            winner_key = (-winner.base_weight, winner.kind.value, winner.observation_ids, winner.identifier_ids)
            if candidate_key < winner_key:
                positive_winner_by_group[factor.independence_group] = index

        results: list[CorrelationFactorResult] = []
        for index, factor in enumerate(prepared):
            veto = factor.kind in VETO_FACTOR_KINDS
            if factor.freshness_status is FactorStatus.EXCLUDED_STALE:
                status = FactorStatus.EXCLUDED_STALE
                applied_weight = 0
            elif factor.base_weight > 0 and positive_winner_by_group.get(factor.independence_group) != index:
                status = FactorStatus.SUPPRESSED_SAME_INDEPENDENCE_GROUP
                applied_weight = 0
            else:
                status = factor.freshness_status
                applied_weight = factor.base_weight

            results.append(
                CorrelationFactorResult(
                    kind=factor.kind,
                    independence_group=factor.independence_group,
                    base_weight=factor.base_weight,
                    applied_weight=applied_weight,
                    status=status,
                    observation_ids=factor.observation_ids,
                    identifier_ids=factor.identifier_ids,
                    rationale=factor.rationale,
                    veto=veto,
                )
            )
        return tuple(results)

    @staticmethod
    def _factor_result_payload(result: CorrelationFactorResult) -> dict[str, object]:
        return {
            "applied_weight": result.applied_weight,
            "base_weight": result.base_weight,
            "identifier_ids": list(result.identifier_ids),
            "independence_group": result.independence_group,
            "kind": result.kind.value,
            "observation_ids": list(result.observation_ids),
            "rationale": result.rationale,
            "status": result.status.value,
            "veto": result.veto,
        }

    @staticmethod
    def _result_from_run(run: CorrelationRun) -> CorrelationResult:
        payload = json.loads(run.normalized_output)
        factors = tuple(
            CorrelationFactorResult(
                kind=FactorKind(item["kind"]),
                independence_group=item["independence_group"],
                base_weight=item["base_weight"],
                applied_weight=item["applied_weight"],
                status=FactorStatus(item["status"]),
                observation_ids=tuple(item["observation_ids"]),
                identifier_ids=tuple(item["identifier_ids"]),
                rationale=item["rationale"],
                veto=item["veto"],
            )
            for item in payload["factors"]
        )
        return CorrelationResult(
            run_id=run.id,
            policy_version=payload["policy_version"],
            subject_id=UUID(payload["subject_id"]),
            candidate_observation_id=UUID(payload["candidate_observation_id"]),
            evaluated_at=payload["evaluated_at"],
            outcome=CorrelationOutcome(payload["outcome"]),
            evidence_score=payload["evidence_score"],
            calibration_status=CalibrationStatus(payload["calibration_status"]),
            positive_independence_groups=payload["positive_independence_groups"],
            factors=factors,
            input_digest=run.input_digest,
            output_digest=run.output_digest,
            normalized_output=run.normalized_output,
            is_identity_claim=payload["is_identity_claim"],
        )
