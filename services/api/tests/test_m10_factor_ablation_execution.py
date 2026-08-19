# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.correlation import (
    CorrelationEngine,
    CorrelationFactorInput,
    CorrelationOutcome,
    CorrelationRequest,
    FactorKind,
)
from app.correlation.models import CorrelationFactorRecord, CorrelationRun
from app.evidence import (
    EvidenceStore,
    IdentifierKind,
    ObservationSourceKind,
    create_database_engine,
    create_schema,
    make_session_factory,
    normalize_identifier,
)
from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_limit_evaluation import GraphLimitScenario
from app.intelligence.m10_factor_ablation import build_m10_factor_ablation_plan
from app.intelligence.m10_factor_ablation_execution import (
    M10FactorAblationCase,
    execute_m10_factor_ablation_plan,
)
from app.intelligence.m10_fixture_library import broadened_synthetic_m10_cohort
from app.intelligence.m10_replay import build_m10_replay_record

EVALUATED_AT = datetime(2026, 8, 19, 3, 0, tzinfo=timezone.utc)


def _plan():
    replay = build_m10_replay_record(
        fixtures=broadened_synthetic_m10_cohort(),
        baseline=GraphLimitScenario(
            "current_depth2_nodes12",
            compatibility_frontier_limits(max_depth=2, max_nodes=12),
        ),
    )
    return build_m10_factor_ablation_plan(replay)


def _candidate(store: EvidenceStore, subject_id, handle: str):
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
        retrieved_at=EVALUATED_AT - timedelta(days=1),
        expires_at=EVALUATED_AT + timedelta(days=30),
    )
    return username, candidate


def _support(store: EvidenceStore, subject_id, candidate_id, name: str, *, confirmed_ids=()):
    payload = {
        "candidate_observation_id": str(candidate_id),
        "synthetic": True,
    }
    if confirmed_ids:
        payload["confirmed_identifier_ids"] = [str(value) for value in confirmed_ids]
    return store.add_observation(
        subject_id=subject_id,
        source_kind=ObservationSourceKind.PUBLIC_WEB,
        source_name=name,
        source_locator=f"https://{name}.example/evidence",
        payload=payload,
        retrieved_at=EVALUATED_AT - timedelta(days=1),
        expires_at=EVALUATED_AT + timedelta(days=30),
    )


def _factor(kind: FactorKind, observation_id, *, identifier_ids=()):
    return CorrelationFactorInput(
        kind=kind,
        observation_ids=(observation_id,),
        identifier_ids=tuple(identifier_ids),
        rationale=f"Synthetic controlled {kind.value} evidence.",
    )


def _build_cases(store: EvidenceStore, subject_id) -> tuple[M10FactorAblationCase, ...]:
    _username, possible = _candidate(store, subject_id, "possible-case")
    possible_metadata = _support(store, subject_id, possible.id, "possible-metadata")
    possible_temporal = _support(store, subject_id, possible.id, "possible-temporal")
    possible_request = CorrelationRequest(
        subject_id=subject_id,
        candidate_observation_id=possible.id,
        evaluated_at=EVALUATED_AT,
        factors=(
            _factor(FactorKind.SAME_USERNAME, possible.id),
            _factor(FactorKind.COMPATIBLE_PROFILE_METADATA, possible_metadata.id),
            _factor(FactorKind.TEMPORAL_COMPATIBILITY, possible_temporal.id),
        ),
    )

    _username, strong_identifier = _candidate(store, subject_id, "identifier-case")
    email = store.add_identifier(
        subject_id,
        normalize_identifier(IdentifierKind.EMAIL, "controlled@example.test"),
    )
    exact_source = _support(
        store,
        subject_id,
        strong_identifier.id,
        "exact-identifier",
        confirmed_ids=(email.id,),
    )
    identifier_temporal = _support(
        store,
        subject_id,
        strong_identifier.id,
        "identifier-temporal",
    )
    identifier_request = CorrelationRequest(
        subject_id=subject_id,
        candidate_observation_id=strong_identifier.id,
        evaluated_at=EVALUATED_AT,
        factors=(
            _factor(FactorKind.SAME_USERNAME, strong_identifier.id),
            _factor(
                FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                exact_source.id,
                identifier_ids=(email.id,),
            ),
            _factor(FactorKind.TEMPORAL_COMPATIBILITY, identifier_temporal.id),
        ),
    )

    _username, strong_cross = _candidate(store, subject_id, "cross-link-case")
    cross_source = _support(store, subject_id, strong_cross.id, "independent-cross")
    cross_metadata = _support(store, subject_id, strong_cross.id, "cross-metadata")
    cross_temporal = _support(store, subject_id, strong_cross.id, "cross-temporal")
    cross_request = CorrelationRequest(
        subject_id=subject_id,
        candidate_observation_id=strong_cross.id,
        evaluated_at=EVALUATED_AT,
        factors=(
            _factor(FactorKind.SAME_USERNAME, strong_cross.id),
            _factor(FactorKind.INDEPENDENT_CROSS_LINK, cross_source.id),
            _factor(FactorKind.COMPATIBLE_PROFILE_METADATA, cross_metadata.id),
            _factor(FactorKind.TEMPORAL_COMPATIBILITY, cross_temporal.id),
        ),
    )

    _username, contradicted = _candidate(store, subject_id, "contradicted-case")
    contradicted_email = store.add_identifier(
        subject_id,
        normalize_identifier(IdentifierKind.EMAIL, "contradicted@example.test"),
    )
    contradicted_exact = _support(
        store,
        subject_id,
        contradicted.id,
        "contradicted-exact",
        confirmed_ids=(contradicted_email.id,),
    )
    contradicted_cross = _support(store, subject_id, contradicted.id, "contradicted-cross")
    contradiction = _support(store, subject_id, contradicted.id, "hard-contradiction")
    contradicted_request = CorrelationRequest(
        subject_id=subject_id,
        candidate_observation_id=contradicted.id,
        evaluated_at=EVALUATED_AT,
        factors=(
            _factor(
                FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
                contradicted_exact.id,
                identifier_ids=(contradicted_email.id,),
            ),
            _factor(FactorKind.INDEPENDENT_CROSS_LINK, contradicted_cross.id),
            _factor(FactorKind.HARD_CONTRADICTION, contradiction.id),
        ),
    )

    return (
        M10FactorAblationCase("possible_metadata_temporal", possible_request),
        M10FactorAblationCase("strong_exact_identifier", identifier_request),
        M10FactorAblationCase("strong_independent_cross_link", cross_request),
        M10FactorAblationCase("contradiction_veto", contradicted_request),
    )


def _scenario(case_result, kind: FactorKind):
    return next(
        item for item in case_result.scenarios if item.omitted_factor_kind is kind
    )


def _assert_no_retained_m5_diagnostics(session) -> None:
    assert session.scalar(select(func.count()).select_from(CorrelationRun)) == 0
    assert session.scalar(select(func.count()).select_from(CorrelationFactorRecord)) == 0


def test_ablation_execution_uses_real_m5_outcomes_and_records_deltas() -> None:
    database = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(database)
    factory = make_session_factory(database)
    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject("Synthetic M10 ablation subject")
        execution = execute_m10_factor_ablation_plan(
            plan=_plan(),
            engine=CorrelationEngine(session),
            cases=_build_cases(store, subject.id),
        )

        by_name = {case.name: case for case in execution.cases}

        possible = by_name["possible_metadata_temporal"]
        assert possible.baseline_outcome is CorrelationOutcome.POSSIBLE_MATCH
        assert possible.baseline_evidence_score == 35
        metadata = _scenario(possible, FactorKind.COMPATIBLE_PROFILE_METADATA)
        assert metadata.factor_present is True
        assert metadata.ablated_outcome is CorrelationOutcome.INSUFFICIENT_EVIDENCE
        assert metadata.evidence_score_delta == -15

        identifier = by_name["strong_exact_identifier"]
        assert identifier.baseline_outcome is CorrelationOutcome.STRONG_CANDIDATE
        assert identifier.baseline_evidence_score == 75
        exact = _scenario(identifier, FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP)
        assert exact.ablated_outcome is CorrelationOutcome.INSUFFICIENT_EVIDENCE
        assert exact.evidence_score_delta == -55

        cross = by_name["strong_independent_cross_link"]
        assert cross.baseline_outcome is CorrelationOutcome.STRONG_CANDIDATE
        assert cross.baseline_evidence_score == 70
        cross_link = _scenario(cross, FactorKind.INDEPENDENT_CROSS_LINK)
        assert cross_link.ablated_outcome is CorrelationOutcome.POSSIBLE_MATCH
        assert cross_link.evidence_score_delta == -35

        vetoed = by_name["contradiction_veto"]
        assert vetoed.baseline_outcome is CorrelationOutcome.CONTRADICTED
        assert vetoed.baseline_evidence_score == 0
        veto = _scenario(vetoed, FactorKind.HARD_CONTRADICTION)
        assert veto.factor_present is True
        assert veto.safety_critical is True
        assert veto.diagnostic_only is True
        assert veto.ablated_outcome is CorrelationOutcome.STRONG_CANDIDATE
        assert veto.ablated_evidence_score == 90
        assert veto.evidence_score_delta == 90
        _assert_no_retained_m5_diagnostics(session)


def test_absent_factor_omission_is_explicit_noop_and_execution_is_repeatable() -> None:
    database = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(database)
    factory = make_session_factory(database)
    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject("Synthetic repeatability subject")
        cases = _build_cases(store, subject.id)
        plan = _plan()
        engine = CorrelationEngine(session)

        first = execute_m10_factor_ablation_plan(plan=plan, engine=engine, cases=cases)
        second = execute_m10_factor_ablation_plan(plan=plan, engine=engine, cases=cases)

        assert first == second
        possible = next(case for case in first.cases if case.name == "possible_metadata_temporal")
        absent_exact = _scenario(possible, FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP)
        assert absent_exact.factor_present is False
        assert absent_exact.evidence_score_delta == 0
        assert absent_exact.ablated_outcome is possible.baseline_outcome
        _assert_no_retained_m5_diagnostics(session)


def test_execution_rejects_tampered_plan_and_invalid_case_contract() -> None:
    database = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(database)
    factory = make_session_factory(database)
    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject("Synthetic validation subject")
        cases = _build_cases(store, subject.id)
        plan = _plan()
        engine = CorrelationEngine(session)

        with pytest.raises(ValueError, match="plan digest"):
            execute_m10_factor_ablation_plan(
                plan=replace(plan, plan_digest="0" * 64),
                engine=engine,
                cases=cases,
            )

        with pytest.raises(ValueError, match="case names must be unique"):
            execute_m10_factor_ablation_plan(
                plan=plan,
                engine=engine,
                cases=(cases[0], cases[0]),
            )

        one_factor = replace(
            cases[0],
            name="invalid_single_factor",
            request=replace(cases[0].request, factors=(cases[0].request.factors[0],)),
        )
        with pytest.raises(ValueError, match="at least two factors"):
            execute_m10_factor_ablation_plan(
                plan=plan,
                engine=engine,
                cases=(one_factor,),
            )
        _assert_no_retained_m5_diagnostics(session)
