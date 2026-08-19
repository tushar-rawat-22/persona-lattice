# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import LeadKind
from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_limit_evaluation import GraphLimitScenario
from app.intelligence.m10_cohort import compare_m10_graph_fixture_cohort
from app.intelligence.m10_fixture_library import broadened_synthetic_m10_cohort


def _scenario(name: str, *, depth: int) -> GraphLimitScenario:
    return GraphLimitScenario(
        name,
        compatibility_frontier_limits(max_depth=depth, max_nodes=12),
    )


def test_broadened_cohort_covers_multiple_seed_kinds_and_policy_shapes() -> None:
    fixtures = broadened_synthetic_m10_cohort()

    assert len(fixtures) == 6
    assert {fixture.seed_kind for fixture in fixtures} == {
        LeadKind.USERNAME,
        LeadKind.EMAIL,
        LeadKind.URL,
        LeadKind.PHONE,
    }
    assert len({fixture.name for fixture in fixtures}) == len(fixtures)

    comparison = compare_m10_graph_fixture_cohort(
        fixtures=fixtures,
        baseline=_scenario("current_depth2_nodes12", depth=2),
        candidates=(_scenario("candidate_depth3_nodes12", depth=3),),
    )

    baseline = comparison.baseline.counters
    candidate = comparison.candidates[0].counters
    delta = comparison.deltas[0]

    assert baseline.fixture_count == 6
    assert baseline.node_count == 15
    assert baseline.added_node_count == 9
    assert baseline.max_observed_depth == 2
    assert baseline.duplicate_suppression_count == 2
    assert baseline.provider_failure_count == 2
    assert baseline.budget_stop_count == 3
    assert baseline.review_required_count == 1
    assert baseline.display_only_count == 0
    assert baseline.blocked_count == 0
    assert baseline.source_attempt_count == 11
    assert baseline.successful_source_attempt_count == 9
    assert baseline.zero_yield_source_attempt_count == 2
    assert baseline.observation_yield_unit_count == 9
    assert baseline.request_cost_unit_count == 11
    assert baseline.labelled_admitted_pivot_count == 9
    assert baseline.wrong_pivot_count == 1
    assert baseline.relevant_pivot_count == 8
    assert baseline.unlabelled_admitted_pivot_count == 0

    assert candidate.fixture_count == 6
    assert candidate.node_count == 18
    assert candidate.added_node_count == 12
    assert candidate.max_observed_depth == 3
    assert candidate.duplicate_suppression_count == 2
    assert candidate.provider_failure_count == 2
    assert candidate.budget_stop_count == 0
    assert candidate.review_required_count == 1
    assert candidate.display_only_count == 0
    assert candidate.blocked_count == 0
    assert candidate.source_attempt_count == 14
    assert candidate.successful_source_attempt_count == 12
    assert candidate.zero_yield_source_attempt_count == 2
    assert candidate.observation_yield_unit_count == 12
    assert candidate.request_cost_unit_count == 14
    assert candidate.labelled_admitted_pivot_count == 12
    assert candidate.wrong_pivot_count == 4
    assert candidate.relevant_pivot_count == 8
    assert candidate.unlabelled_admitted_pivot_count == 0

    assert delta.node_delta == 3
    assert delta.added_node_delta == 3
    assert delta.max_observed_depth_delta == 1
    assert delta.duplicate_suppression_delta == 0
    assert delta.provider_failure_delta == 0
    assert delta.budget_stop_delta == -3
    assert delta.review_required_delta == 0
    assert delta.display_only_delta == 0
    assert delta.blocked_delta == 0
    assert delta.source_attempt_delta == 3
    assert delta.successful_source_attempt_delta == 3
    assert delta.zero_yield_source_attempt_delta == 0
    assert delta.observation_yield_unit_delta == 3
    assert delta.request_cost_unit_delta == 3
    assert delta.labelled_admitted_pivot_delta == 3
    assert delta.wrong_pivot_delta == 3
    assert delta.relevant_pivot_delta == 0
    assert delta.unlabelled_admitted_pivot_delta == 0


def test_operational_units_count_only_frontier_approved_source_attempts() -> None:
    comparison = compare_m10_graph_fixture_cohort(
        fixtures=broadened_synthetic_m10_cohort(),
        baseline=_scenario("current", depth=2),
        candidates=(),
    )
    counters = comparison.baseline.counters

    assert counters.source_attempt_count == (
        counters.successful_source_attempt_count + counters.zero_yield_source_attempt_count
    )
    assert counters.successful_source_attempt_count == counters.added_node_count
    assert counters.zero_yield_source_attempt_count == counters.provider_failure_count
    assert counters.observation_yield_unit_count == counters.successful_source_attempt_count
    assert counters.request_cost_unit_count == counters.source_attempt_count
    assert (
        counters.duplicate_suppression_count
        + counters.review_required_count
        + counters.budget_stop_count
        > 0
    )


def test_broadened_cohort_does_not_change_production_frontier_limits() -> None:
    current = compatibility_frontier_limits(max_depth=2, max_nodes=12)
    fixtures = broadened_synthetic_m10_cohort()

    comparison = compare_m10_graph_fixture_cohort(
        fixtures=fixtures,
        baseline=GraphLimitScenario("current", current),
        candidates=(),
    )

    assert comparison.baseline.scenario.limits.max_depth == 2
    assert comparison.baseline.scenario.limits.max_nodes == 12
    assert comparison.candidates == ()
    assert comparison.deltas == ()
