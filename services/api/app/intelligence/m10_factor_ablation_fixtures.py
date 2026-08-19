# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.correlation import CorrelationFactorInput, CorrelationRequest, FactorKind
from app.evidence import EvidenceStore, IdentifierKind, ObservationSourceKind, normalize_identifier

from .m10_factor_ablation_execution import M10FactorAblationCase, M10FactorAblationExecution

_FIXTURE_SCHEMA_VERSION = 1
_REPLAY_SCHEMA_VERSION = 1
_DEFAULT_EVALUATED_AT = datetime(2026, 8, 19, 3, 0, tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class M10FactorEvidenceSpec:
    """UUID-independent description of one controlled M5 factor input."""

    kind: FactorKind
    source_name: str | None = None
    confirmed_identifier_kind: IdentifierKind | None = None
    confirmed_identifier_value: str | None = None


@dataclass(frozen=True, slots=True)
class M10FactorAblationCaseSpec:
    """Stable semantic definition of one controlled factor-ablation case."""

    name: str
    candidate_handle: str
    factors: tuple[M10FactorEvidenceSpec, ...]


@dataclass(frozen=True, slots=True)
class M10FactorAblationFixtureSet:
    """Versioned controlled case set with a UUID-independent semantic fingerprint."""

    schema_version: int
    evaluated_at: datetime
    cases: tuple[M10FactorAblationCaseSpec, ...]
    fixture_digest: str


@dataclass(frozen=True, slots=True)
class M10FactorAblationReplayRecord:
    """Reproducible identity for one factor-ablation execution result."""

    schema_version: int
    plan_digest: str
    fixture_digest: str
    result_digest: str


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _factor_spec_payload(spec: M10FactorEvidenceSpec) -> dict[str, object]:
    return {
        "kind": spec.kind.value,
        "source_name": spec.source_name,
        "confirmed_identifier_kind": (
            None if spec.confirmed_identifier_kind is None else spec.confirmed_identifier_kind.value
        ),
        "confirmed_identifier_value": spec.confirmed_identifier_value,
    }


def _case_spec_payload(spec: M10FactorAblationCaseSpec) -> dict[str, object]:
    return {
        "name": spec.name,
        "candidate_handle": spec.candidate_handle,
        # Factor order is retained because production M5 receives an ordered request tuple.
        "factors": [_factor_spec_payload(factor) for factor in spec.factors],
    }


def _case_semantic_digest(spec: M10FactorAblationCaseSpec, evaluated_at: datetime) -> str:
    return _sha256_json(
        {
            "schema_version": _FIXTURE_SCHEMA_VERSION,
            "evaluated_at": evaluated_at.isoformat(),
            "case": _case_spec_payload(spec),
        }
    )


def _validate_case_specs(cases: tuple[M10FactorAblationCaseSpec, ...]) -> None:
    if not cases:
        raise ValueError("At least one controlled M10 factor-ablation case spec is required.")
    names: set[str] = set()
    for case in cases:
        if not case.name or case.name.strip() != case.name:
            raise ValueError("Controlled M10 case names must be non-empty and trimmed.")
        if case.name in names:
            raise ValueError("Controlled M10 case names must be unique.")
        names.add(case.name)
        if not case.candidate_handle or case.candidate_handle.strip() != case.candidate_handle:
            raise ValueError("Controlled M10 candidate handles must be non-empty and trimmed.")
        if len(case.factors) < 2:
            raise ValueError("Controlled M10 cases require at least two factor specs.")
        factor_kinds = tuple(factor.kind for factor in case.factors)
        if len(set(factor_kinds)) != len(factor_kinds):
            raise ValueError("Controlled M10 cases may declare each factor kind at most once.")
        for factor in case.factors:
            is_same_username = factor.kind is FactorKind.SAME_USERNAME
            if is_same_username:
                if factor.source_name is not None:
                    raise ValueError("same_username uses the candidate observation, not a support source.")
                if factor.confirmed_identifier_kind is not None or factor.confirmed_identifier_value is not None:
                    raise ValueError("same_username cannot declare a confirmed identifier.")
                continue
            if not factor.source_name or factor.source_name.strip() != factor.source_name:
                raise ValueError("Non-candidate controlled factors require a trimmed source name.")
            has_kind = factor.confirmed_identifier_kind is not None
            has_value = factor.confirmed_identifier_value is not None
            if has_kind != has_value:
                raise ValueError("Confirmed identifier kind/value must be declared together.")
            if has_kind and factor.kind is not FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP:
                raise ValueError("Only exact identifier overlap fixtures may declare a confirmed identifier.")


def controlled_m5_factor_ablation_specs() -> tuple[M10FactorAblationCaseSpec, ...]:
    """Return the reusable semantic M5 cases used for controlled ablation measurement."""

    return (
        M10FactorAblationCaseSpec(
            name="possible_metadata_temporal",
            candidate_handle="possible-case",
            factors=(
                M10FactorEvidenceSpec(FactorKind.SAME_USERNAME),
                M10FactorEvidenceSpec(FactorKind.COMPATIBLE_PROFILE_METADATA, "possible-metadata"),
                M10FactorEvidenceSpec(FactorKind.TEMPORAL_COMPATIBILITY, "possible-temporal"),
            ),
        ),
        M10FactorAblationCaseSpec(
            name="strong_exact_identifier",
            candidate_handle="identifier-case",
            factors=(
                M10FactorEvidenceSpec(FactorKind.SAME_USERNAME),
                M10FactorEvidenceSpec(
                    FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                    "exact-identifier",
                    IdentifierKind.EMAIL,
                    "controlled@example.test",
                ),
                M10FactorEvidenceSpec(FactorKind.TEMPORAL_COMPATIBILITY, "identifier-temporal"),
            ),
        ),
        M10FactorAblationCaseSpec(
            name="strong_independent_cross_link",
            candidate_handle="cross-link-case",
            factors=(
                M10FactorEvidenceSpec(FactorKind.SAME_USERNAME),
                M10FactorEvidenceSpec(FactorKind.INDEPENDENT_CROSS_LINK, "independent-cross"),
                M10FactorEvidenceSpec(FactorKind.COMPATIBLE_PROFILE_METADATA, "cross-metadata"),
                M10FactorEvidenceSpec(FactorKind.TEMPORAL_COMPATIBILITY, "cross-temporal"),
            ),
        ),
        M10FactorAblationCaseSpec(
            name="contradiction_veto",
            candidate_handle="contradicted-case",
            factors=(
                M10FactorEvidenceSpec(
                    FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                    "contradicted-exact",
                    IdentifierKind.EMAIL,
                    "contradicted@example.test",
                ),
                M10FactorEvidenceSpec(FactorKind.INDEPENDENT_CROSS_LINK, "contradicted-cross"),
                M10FactorEvidenceSpec(FactorKind.HARD_CONTRADICTION, "hard-contradiction"),
            ),
        ),
    )


def build_m10_factor_ablation_fixture_set(
    *,
    cases: tuple[M10FactorAblationCaseSpec, ...] | None = None,
    evaluated_at: datetime = _DEFAULT_EVALUATED_AT,
) -> M10FactorAblationFixtureSet:
    """Build a stable case-set identity without including database-generated UUIDs."""

    prepared = controlled_m5_factor_ablation_specs() if cases is None else tuple(cases)
    _validate_case_specs(prepared)
    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise ValueError("M10 controlled evaluation time must be timezone-aware.")
    normalized_time = evaluated_at.astimezone(timezone.utc)
    payload = {
        "schema_version": _FIXTURE_SCHEMA_VERSION,
        "evaluated_at": normalized_time.isoformat(),
        # Case ordering does not affect independent case execution, so canonicalize it.
        "cases": [_case_spec_payload(case) for case in sorted(prepared, key=lambda item: item.name)],
    }
    return M10FactorAblationFixtureSet(
        schema_version=_FIXTURE_SCHEMA_VERSION,
        evaluated_at=normalized_time,
        cases=prepared,
        fixture_digest=_sha256_json(payload),
    )


def _candidate(store: EvidenceStore, subject_id: UUID, handle: str, evaluated_at: datetime):
    username = store.add_identifier(
        subject_id,
        normalize_identifier(IdentifierKind.USERNAME, handle),
    )
    candidate = store.add_observation(
        subject_id=subject_id,
        identifier_id=username.id,
        source_kind=ObservationSourceKind.PROVIDER,
        source_name="synthetic-candidate",
        source_locator=f"https://profiles.example/{handle}",
        payload={"account_candidate": True, "identity_claim": False},
        retrieved_at=evaluated_at - timedelta(days=1),
        expires_at=evaluated_at + timedelta(days=30),
    )
    return candidate


def _support(
    store: EvidenceStore,
    subject_id: UUID,
    candidate_id: UUID,
    source_name: str,
    evaluated_at: datetime,
    *,
    confirmed_ids: tuple[UUID, ...] = (),
):
    payload: dict[str, object] = {
        "candidate_observation_id": str(candidate_id),
        "synthetic": True,
    }
    if confirmed_ids:
        payload["confirmed_identifier_ids"] = [str(value) for value in confirmed_ids]
    return store.add_observation(
        subject_id=subject_id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name=source_name,
        source_locator=f"https://{source_name}.example/evidence",
        payload=payload,
        retrieved_at=evaluated_at - timedelta(days=1),
        expires_at=evaluated_at + timedelta(days=30),
    )


def materialize_m10_factor_ablation_cases(
    *,
    fixture_set: M10FactorAblationFixtureSet,
    store: EvidenceStore,
    subject_id: UUID,
) -> tuple[M10FactorAblationCase, ...]:
    """Materialize one semantic fixture set into fresh evidence rows for the real M5 engine."""

    if fixture_set.schema_version != _FIXTURE_SCHEMA_VERSION:
        raise ValueError("Unsupported M10 controlled fixture schema version.")
    expected = build_m10_factor_ablation_fixture_set(
        cases=fixture_set.cases,
        evaluated_at=fixture_set.evaluated_at,
    )
    if fixture_set.fixture_digest != expected.fixture_digest:
        raise ValueError("M10 controlled fixture digest does not match its semantic definition.")

    materialized: list[M10FactorAblationCase] = []
    for case in fixture_set.cases:
        candidate = _candidate(store, subject_id, case.candidate_handle, fixture_set.evaluated_at)
        factor_inputs: list[CorrelationFactorInput] = []
        for factor in case.factors:
            if factor.kind is FactorKind.SAME_USERNAME:
                factor_inputs.append(
                    CorrelationFactorInput(
                        kind=factor.kind,
                        observation_ids=(candidate.id,),
                        rationale=f"Synthetic controlled {factor.kind.value} evidence.",
                    )
                )
                continue

            identifier_ids: tuple[UUID, ...] = ()
            if factor.confirmed_identifier_kind is not None:
                assert factor.confirmed_identifier_value is not None
                identifier = store.add_identifier(
                    subject_id,
                    normalize_identifier(
                        factor.confirmed_identifier_kind,
                        factor.confirmed_identifier_value,
                    ),
                )
                identifier_ids = (identifier.id,)
            assert factor.source_name is not None
            support = _support(
                store,
                subject_id,
                candidate.id,
                factor.source_name,
                fixture_set.evaluated_at,
                confirmed_ids=identifier_ids,
            )
            factor_inputs.append(
                CorrelationFactorInput(
                    kind=factor.kind,
                    observation_ids=(support.id,),
                    identifier_ids=identifier_ids,
                    rationale=f"Synthetic controlled {factor.kind.value} evidence.",
                )
            )

        materialized.append(
            M10FactorAblationCase(
                name=case.name,
                request=CorrelationRequest(
                    subject_id=subject_id,
                    candidate_observation_id=candidate.id,
                    evaluated_at=fixture_set.evaluated_at,
                    factors=tuple(factor_inputs),
                ),
                semantic_case_digest=_case_semantic_digest(case, fixture_set.evaluated_at),
            )
        )
    return tuple(materialized)


def _execution_payload(execution: M10FactorAblationExecution) -> dict[str, object]:
    return {
        "schema_version": execution.schema_version,
        "plan_digest": execution.plan_digest,
        "m5_policy_version": execution.m5_policy_version,
        "m5_policy_digest": execution.m5_policy_digest,
        "cases": [
            {
                "name": case.name,
                "semantic_case_digest": case.semantic_case_digest,
                "baseline_outcome": case.baseline_outcome.value,
                "baseline_evidence_score": case.baseline_evidence_score,
                "baseline_positive_independence_groups": case.baseline_positive_independence_groups,
                "scenarios": [
                    {
                        "scenario_name": scenario.scenario_name,
                        "omitted_factor_kind": scenario.omitted_factor_kind.value,
                        "diagnostic_only": scenario.diagnostic_only,
                        "safety_critical": scenario.safety_critical,
                        "factor_present": scenario.factor_present,
                        "ablated_outcome": scenario.ablated_outcome.value,
                        "ablated_evidence_score": scenario.ablated_evidence_score,
                        "ablated_positive_independence_groups": scenario.ablated_positive_independence_groups,
                        "evidence_score_delta": scenario.evidence_score_delta,
                        "positive_independence_groups_delta": scenario.positive_independence_groups_delta,
                    }
                    for scenario in sorted(case.scenarios, key=lambda item: item.scenario_name)
                ],
            }
            for case in sorted(execution.cases, key=lambda item: item.name)
        ],
    }


def build_m10_factor_ablation_replay_record(
    *,
    fixture_set: M10FactorAblationFixtureSet,
    execution: M10FactorAblationExecution,
) -> M10FactorAblationReplayRecord:
    """Fingerprint controlled M5 results without including run or evidence UUIDs."""

    if fixture_set.schema_version != _FIXTURE_SCHEMA_VERSION:
        raise ValueError("Unsupported M10 controlled fixture schema version.")
    expected_fixture = build_m10_factor_ablation_fixture_set(
        cases=fixture_set.cases,
        evaluated_at=fixture_set.evaluated_at,
    )
    if fixture_set.fixture_digest != expected_fixture.fixture_digest:
        raise ValueError("M10 controlled fixture digest does not match its semantic definition.")

    expected_case_digests = {
        case.name: _case_semantic_digest(case, fixture_set.evaluated_at)
        for case in fixture_set.cases
    }
    actual_case_digests = {
        case.name: case.semantic_case_digest
        for case in execution.cases
    }
    if (
        set(actual_case_digests) != set(expected_case_digests)
        or len(execution.cases) != len(expected_case_digests)
    ):
        raise ValueError("M10 ablation execution cases do not match the controlled fixture set.")
    if actual_case_digests != expected_case_digests:
        raise ValueError("M10 ablation execution case fingerprints do not match the controlled fixture set.")

    return M10FactorAblationReplayRecord(
        schema_version=_REPLAY_SCHEMA_VERSION,
        plan_digest=execution.plan_digest,
        fixture_digest=fixture_set.fixture_digest,
        result_digest=_sha256_json(_execution_payload(execution)),
    )
