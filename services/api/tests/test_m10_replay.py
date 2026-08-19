# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import replace

from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_evaluation import PivotRelevance
from app.intelligence.graph_limit_evaluation import GraphLimitScenario
from app.intelligence.m10_fixture_library import broadened_synthetic_m10_cohort
from app.intelligence.m10_replay import build_m10_replay_record


def _scenario(name: str, *, depth: int) -> GraphLimitScenario:
    return GraphLimitScenario(
        name,
        compatibility_frontier_limits(max_depth=depth, max_nodes=12),
    )


def test_replay_digest_is_stable_across_top_level_input_order() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    baseline = _scenario("current_depth2_nodes12", depth=2)
    candidate = _scenario("candidate_depth3_nodes12", depth=3)

    first = build_m10_replay_record(
        fixtures=fixtures,
        baseline=baseline,
        candidates=(candidate,),
    )
    replay = build_m10_replay_record(
        fixtures=tuple(reversed(fixtures)),
        baseline=baseline,
        candidates=(candidate,),
    )

    assert first.schema_version == 1
    assert len(first.input_digest) == 64
    assert len(first.result_digest) == 64
    assert first.input_digest == replay.input_digest
    assert first.result_digest == replay.result_digest
    assert first.comparison == replay.comparison


def test_replay_digest_changes_when_fixture_truth_changes() -> None:
    fixtures = list(broadened_synthetic_m10_cohort())
    fixture = fixtures[0]
    key = next(iter(fixture.pivot_relevance_by_key))
    original = fixture.pivot_relevance_by_key[key]
    changed = (
        PivotRelevance.WRONG
        if original is PivotRelevance.RELEVANT
        else PivotRelevance.RELEVANT
    )
    relevance = dict(fixture.pivot_relevance_by_key)
    relevance[key] = changed
    fixtures[0] = replace(fixture, pivot_relevance_by_key=relevance)

    baseline = _scenario("current_depth2_nodes12", depth=2)
    original_record = build_m10_replay_record(
        fixtures=broadened_synthetic_m10_cohort(),
        baseline=baseline,
    )
    changed_record = build_m10_replay_record(
        fixtures=fixtures,
        baseline=baseline,
    )

    assert original_record.input_digest != changed_record.input_digest
    assert original_record.result_digest != changed_record.result_digest


def test_replay_digest_changes_when_frontier_policy_changes() -> None:
    fixtures = broadened_synthetic_m10_cohort()

    depth2 = build_m10_replay_record(
        fixtures=fixtures,
        baseline=_scenario("current", depth=2),
    )
    depth3 = build_m10_replay_record(
        fixtures=fixtures,
        baseline=_scenario("current", depth=3),
    )

    assert depth2.input_digest != depth3.input_digest
    assert depth2.result_digest != depth3.result_digest
    assert depth2.comparison.baseline.counters != depth3.comparison.baseline.counters


def test_replay_record_does_not_change_production_frontier_limits() -> None:
    record = build_m10_replay_record(
        fixtures=broadened_synthetic_m10_cohort(),
        baseline=_scenario("current", depth=2),
        candidates=(_scenario("candidate", depth=3),),
    )

    assert record.comparison.baseline.scenario.limits.max_depth == 2
    assert record.comparison.baseline.scenario.limits.max_nodes == 12
    assert record.comparison.candidates[0].scenario.limits.max_depth == 3
    assert record.comparison.candidates[0].scenario.limits.max_nodes == 12
