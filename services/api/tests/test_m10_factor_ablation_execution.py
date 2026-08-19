# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy import func, select

from app.correlation import CorrelationEngine, CorrelationOutcome, FactorKind
from app.correlation.models import CorrelationFactorRecord, CorrelationRun
from app.evidence import EvidenceStore, create_database_engine, create_schema, make_session_factory
from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_limit_evaluation import GraphLimitScenario
from app.intelligence.m10_factor_ablation import build_m10_factor_ablation_plan
from app.intelligence.m10_factor_ablation_execution import execute_m10_factor_ablation_plan
from app.intelligence.m10_factor_ablation_fixtures import (
    build_m10_factor_ablation_fixture_set,
    materialize_m10_factor_ablation_cases,
)
from app.intelligence.m10_fixture_library import broadened_synthetic_m10_cohort
from app.intelligence.m10_replay import build_m10_replay_record


def _plan():
    replay = build_m10_replay_record(
        fixtures=broadened_synthetic_m10_cohort(),
        baseline=GraphLimitScenario(
            "current_depth2_nodes12",
            compatibility_frontier_limits(max_depth=2, max_nodes=12),
        ),
    )
    return build_m10_factor_ablation_plan(replay)


def _build_cases(store: EvidenceStore, subject_id):
    return materialize_m10_factor_ablation_cases(
        fixture_set=build_m10_factor_ablation_fixture_set(),
        store=store,
        subject_id=subject_id,
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
