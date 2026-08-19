# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import replace

import pytest

from app.correlation.policy import FACTOR_WEIGHTS, M5_POLICY_VERSION, VETO_FACTOR_KINDS
from app.correlation.types import FactorKind
from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_evaluation import PivotRelevance
from app.intelligence.graph_limit_evaluation import GraphLimitScenario
from app.intelligence.m10_factor_ablation import build_m10_factor_ablation_plan
from app.intelligence.m10_fixture_library import broadened_synthetic_m10_cohort
from app.intelligence.m10_replay import M10ReplayRecord, build_m10_replay_record


def _replay() -> M10ReplayRecord:
    return build_m10_replay_record(
        fixtures=broadened_synthetic_m10_cohort(),
        baseline=GraphLimitScenario(
            "current_depth2_nodes12",
            compatibility_frontier_limits(max_depth=2, max_nodes=12),
        ),
    )


def test_ablation_plan_is_deterministic_and_covers_exact_factor_vocabulary() -> None:
    first = build_m10_factor_ablation_plan(_replay())
    second = build_m10_factor_ablation_plan(_replay())

    assert first == second
    assert first.schema_version == 1
    assert first.m5_policy_version == M5_POLICY_VERSION
    assert len(first.m5_policy_digest) == 64
    assert len(first.plan_digest) == 64
    assert tuple(scenario.omitted_factor_kind for scenario in first.scenarios) == tuple(
        sorted(FactorKind, key=lambda item: item.value)
    )
    assert len({scenario.name for scenario in first.scenarios}) == len(FactorKind)


def test_ablation_scenarios_are_diagnostic_and_flag_veto_removal_as_safety_critical() -> None:
    plan = build_m10_factor_ablation_plan(_replay())

    assert all(scenario.diagnostic_only for scenario in plan.scenarios)
    assert {
        scenario.omitted_factor_kind
        for scenario in plan.scenarios
        if scenario.safety_critical
    } == set(VETO_FACTOR_KINDS)
    hard_contradiction = next(
        scenario
        for scenario in plan.scenarios
        if scenario.omitted_factor_kind is FactorKind.HARD_CONTRADICTION
    )
    assert hard_contradiction.safety_critical is True


def test_ablation_plan_changes_when_replay_fixture_truth_changes() -> None:
    original = _replay()
    fixtures = list(broadened_synthetic_m10_cohort())
    fixture = fixtures[0]
    key = next(iter(fixture.pivot_relevance_by_key))
    changed_relevance = dict(fixture.pivot_relevance_by_key)
    changed_relevance[key] = (
        PivotRelevance.WRONG
        if changed_relevance[key] is PivotRelevance.RELEVANT
        else PivotRelevance.RELEVANT
    )
    fixtures[0] = replace(fixture, pivot_relevance_by_key=changed_relevance)
    changed = build_m10_replay_record(
        fixtures=fixtures,
        baseline=original.comparison.baseline.scenario,
    )

    original_plan = build_m10_factor_ablation_plan(original)
    changed_plan = build_m10_factor_ablation_plan(changed)

    assert original_plan.baseline_replay_input_digest != changed_plan.baseline_replay_input_digest
    assert original_plan.baseline_replay_result_digest != changed_plan.baseline_replay_result_digest
    assert original_plan.plan_digest != changed_plan.plan_digest


def test_ablation_policy_anchor_changes_when_m5_weight_changes(monkeypatch) -> None:
    replay = _replay()
    original = build_m10_factor_ablation_plan(replay)
    kind = FactorKind.SAME_USERNAME

    monkeypatch.setitem(FACTOR_WEIGHTS, kind, FACTOR_WEIGHTS[kind] + 1)
    changed = build_m10_factor_ablation_plan(replay)

    assert original.baseline_replay_input_digest == changed.baseline_replay_input_digest
    assert original.baseline_replay_result_digest == changed.baseline_replay_result_digest
    assert original.m5_policy_digest != changed.m5_policy_digest
    assert original.plan_digest != changed.plan_digest


def test_ablation_plan_rejects_untrusted_replay_identity() -> None:
    replay = _replay()

    with pytest.raises(ValueError, match="input digest"):
        build_m10_factor_ablation_plan(replace(replay, input_digest="not-a-digest"))
    with pytest.raises(ValueError, match="result digest"):
        build_m10_factor_ablation_plan(replace(replay, result_digest="0" * 63))
    with pytest.raises(ValueError, match="schema version"):
        build_m10_factor_ablation_plan(replace(replay, schema_version=999))
