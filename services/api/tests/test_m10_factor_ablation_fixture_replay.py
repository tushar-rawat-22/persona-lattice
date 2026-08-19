# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import replace

import pytest

from app.correlation import CorrelationEngine
from app.evidence import EvidenceStore, create_database_engine, create_schema, make_session_factory
from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_limit_evaluation import GraphLimitScenario
from app.intelligence.m10_factor_ablation import build_m10_factor_ablation_plan
from app.intelligence.m10_factor_ablation_execution import execute_m10_factor_ablation_plan
from app.intelligence.m10_factor_ablation_fixtures import (
    build_m10_factor_ablation_fixture_set,
    build_m10_factor_ablation_replay_record,
    controlled_m5_factor_ablation_specs,
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


def _execute_once(subject_label: str):
    database = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(database)
    factory = make_session_factory(database)
    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject(subject_label)
        fixture_set = build_m10_factor_ablation_fixture_set()
        cases = materialize_m10_factor_ablation_cases(
            fixture_set=fixture_set,
            store=store,
            subject_id=subject.id,
        )
        execution = execute_m10_factor_ablation_plan(
            plan=_plan(),
            engine=CorrelationEngine(session),
            cases=cases,
        )
        replay = build_m10_factor_ablation_replay_record(
            fixture_set=fixture_set,
            execution=execution,
        )
        request_ids = tuple(
            (case.request.subject_id, case.request.candidate_observation_id)
            for case in cases
        )
        return fixture_set, replay, request_ids


def test_controlled_fixture_and_result_digests_survive_fresh_database_uuids() -> None:
    first_fixture, first_replay, first_ids = _execute_once("M10 replay subject A")
    second_fixture, second_replay, second_ids = _execute_once("M10 replay subject B")

    assert first_ids != second_ids
    assert first_fixture.fixture_digest == second_fixture.fixture_digest
    assert first_replay.fixture_digest == second_replay.fixture_digest
    assert first_replay.result_digest == second_replay.result_digest
    assert first_replay.plan_digest == second_replay.plan_digest


def test_fixture_digest_is_case_order_independent_but_factor_order_sensitive() -> None:
    specs = controlled_m5_factor_ablation_specs()
    baseline = build_m10_factor_ablation_fixture_set(cases=specs)
    reordered_cases = build_m10_factor_ablation_fixture_set(cases=tuple(reversed(specs)))

    assert baseline.fixture_digest == reordered_cases.fixture_digest

    changed_factor_order = replace(specs[0], factors=tuple(reversed(specs[0].factors)))
    changed = build_m10_factor_ablation_fixture_set(
        cases=(changed_factor_order, *specs[1:])
    )
    assert changed.fixture_digest != baseline.fixture_digest


def test_fixture_digest_changes_with_semantic_truth_and_tampering_fails_closed() -> None:
    specs = controlled_m5_factor_ablation_specs()
    baseline = build_m10_factor_ablation_fixture_set(cases=specs)
    changed_handle = replace(specs[0], candidate_handle="different-possible-case")
    changed = build_m10_factor_ablation_fixture_set(cases=(changed_handle, *specs[1:]))

    assert changed.fixture_digest != baseline.fixture_digest

    database = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(database)
    factory = make_session_factory(database)
    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject("Tamper validation subject")
        with pytest.raises(ValueError, match="fixture digest"):
            materialize_m10_factor_ablation_cases(
                fixture_set=replace(baseline, fixture_digest="0" * 64),
                store=store,
                subject_id=subject.id,
            )


def test_result_replay_rejects_execution_case_set_drift() -> None:
    database = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(database)
    factory = make_session_factory(database)
    with factory() as session:
        store = EvidenceStore(session)
        subject = store.add_subject("Result drift subject")
        fixture_set = build_m10_factor_ablation_fixture_set()
        cases = materialize_m10_factor_ablation_cases(
            fixture_set=fixture_set,
            store=store,
            subject_id=subject.id,
        )
        execution = execute_m10_factor_ablation_plan(
            plan=_plan(),
            engine=CorrelationEngine(session),
            cases=cases,
        )
        with pytest.raises(ValueError, match="do not match"):
            build_m10_factor_ablation_replay_record(
                fixture_set=fixture_set,
                execution=replace(execution, cases=execution.cases[:-1]),
            )
