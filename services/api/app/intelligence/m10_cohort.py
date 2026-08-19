# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .contracts import LeadKind
from .graph_evaluation import PivotRelevance
from .graph_limit_evaluation import (
    GraphFixtureLead,
    GraphLimitScenario,
    evaluate_graph_limit_fixture_with_operations,
)


@dataclass(frozen=True, slots=True)
class M10GraphFixture:
    """One labelled synthetic or consented graph fixture for M10 comparison."""

    name: str
    seed_key: str
    seed_kind: LeadKind
    leads_by_parent: Mapping[str, Sequence[GraphFixtureLead]]
    pivot_relevance_by_key: Mapping[str, PivotRelevance]

    def __post_init__(self) -> None:
        if not self.name or self.name.strip() != self.name:
            raise ValueError("M10 fixture name must be non-empty and trimmed.")


@dataclass(frozen=True, slots=True)
class M10CohortCounters:
    """Count-only cohort totals; no rates, confidence, or probability claims."""

    fixture_count: int
    node_count: int
    added_node_count: int
    max_observed_depth: int
    duplicate_suppression_count: int
    provider_failure_count: int
    budget_stop_count: int
    review_required_count: int
    display_only_count: int
    blocked_count: int
    source_attempt_count: int
    successful_source_attempt_count: int
    zero_yield_source_attempt_count: int
    observation_yield_unit_count: int
    request_cost_unit_count: int
    labelled_admitted_pivot_count: int
    wrong_pivot_count: int
    relevant_pivot_count: int
    unlabelled_admitted_pivot_count: int


@dataclass(frozen=True, slots=True)
class M10CohortScenarioResult:
    scenario: GraphLimitScenario
    counters: M10CohortCounters


@dataclass(frozen=True, slots=True)
class M10CohortDelta:
    scenario_name: str
    node_delta: int
    added_node_delta: int
    max_observed_depth_delta: int
    duplicate_suppression_delta: int
    provider_failure_delta: int
    budget_stop_delta: int
    review_required_delta: int
    display_only_delta: int
    blocked_delta: int
    source_attempt_delta: int
    successful_source_attempt_delta: int
    zero_yield_source_attempt_delta: int
    observation_yield_unit_delta: int
    request_cost_unit_delta: int
    labelled_admitted_pivot_delta: int
    wrong_pivot_delta: int
    relevant_pivot_delta: int
    unlabelled_admitted_pivot_delta: int


@dataclass(frozen=True, slots=True)
class M10CohortComparison:
    baseline: M10CohortScenarioResult
    candidates: tuple[M10CohortScenarioResult, ...]
    deltas: tuple[M10CohortDelta, ...]


def _evaluate_scenario(
    fixtures: tuple[M10GraphFixture, ...],
    scenario: GraphLimitScenario,
) -> M10CohortScenarioResult:
    results = tuple(
        evaluate_graph_limit_fixture_with_operations(
            seed_key=fixture.seed_key,
            seed_kind=fixture.seed_kind,
            leads_by_parent=fixture.leads_by_parent,
            pivot_relevance_by_key=fixture.pivot_relevance_by_key,
            limits=scenario.limits,
        )
        for fixture in fixtures
    )
    graphs = tuple(item.graph for item in results)
    operations = tuple(item.operational for item in results)
    return M10CohortScenarioResult(
        scenario=scenario,
        counters=M10CohortCounters(
            fixture_count=len(results),
            node_count=sum(item.node_count for item in graphs),
            added_node_count=sum(item.added_node_count for item in graphs),
            max_observed_depth=max(item.max_observed_depth for item in graphs),
            duplicate_suppression_count=sum(
                item.duplicate_suppression_count for item in graphs
            ),
            provider_failure_count=sum(item.provider_failure_count for item in graphs),
            budget_stop_count=sum(item.budget_stop_count for item in graphs),
            review_required_count=sum(item.review_required_count for item in graphs),
            display_only_count=sum(item.display_only_count for item in graphs),
            blocked_count=sum(item.blocked_count for item in graphs),
            source_attempt_count=sum(item.source_attempt_count for item in operations),
            successful_source_attempt_count=sum(
                item.successful_source_attempt_count for item in operations
            ),
            zero_yield_source_attempt_count=sum(
                item.zero_yield_source_attempt_count for item in operations
            ),
            observation_yield_unit_count=sum(
                item.observation_yield_unit_count for item in operations
            ),
            request_cost_unit_count=sum(item.request_cost_unit_count for item in operations),
            labelled_admitted_pivot_count=sum(
                item.labelled_admitted_pivot_count for item in graphs
            ),
            wrong_pivot_count=sum(item.wrong_pivot_count for item in graphs),
            relevant_pivot_count=sum(item.relevant_pivot_count for item in graphs),
            unlabelled_admitted_pivot_count=sum(
                item.unlabelled_admitted_pivot_count for item in graphs
            ),
        ),
    )


def compare_m10_graph_fixture_cohort(
    *,
    fixtures: Sequence[M10GraphFixture],
    baseline: GraphLimitScenario,
    candidates: Sequence[GraphLimitScenario],
) -> M10CohortComparison:
    """Compare frontier policies across a labelled fixture cohort.

    This function is deliberately descriptive. It aggregates deterministic counts
    across independent fixture families and does not recommend a production limit,
    calculate reliability percentages, convert labels into identity probability, or
    treat request-cost units as money.
    """

    fixture_tuple = tuple(fixtures)
    if not fixture_tuple:
        raise ValueError("M10 cohort comparison requires at least one fixture.")
    fixture_names = [fixture.name for fixture in fixture_tuple]
    if len(set(fixture_names)) != len(fixture_names):
        raise ValueError("M10 fixture names must be unique within a cohort.")

    candidate_tuple = tuple(candidates)
    scenario_names = [baseline.name, *(scenario.name for scenario in candidate_tuple)]
    if len(set(scenario_names)) != len(scenario_names):
        raise ValueError("M10 scenario names must be unique within a cohort comparison.")

    baseline_result = _evaluate_scenario(fixture_tuple, baseline)
    candidate_results = tuple(
        _evaluate_scenario(fixture_tuple, scenario) for scenario in candidate_tuple
    )
    base = baseline_result.counters
    deltas = tuple(
        M10CohortDelta(
            scenario_name=result.scenario.name,
            node_delta=result.counters.node_count - base.node_count,
            added_node_delta=result.counters.added_node_count - base.added_node_count,
            max_observed_depth_delta=(
                result.counters.max_observed_depth - base.max_observed_depth
            ),
            duplicate_suppression_delta=(
                result.counters.duplicate_suppression_count
                - base.duplicate_suppression_count
            ),
            provider_failure_delta=(
                result.counters.provider_failure_count - base.provider_failure_count
            ),
            budget_stop_delta=result.counters.budget_stop_count - base.budget_stop_count,
            review_required_delta=(
                result.counters.review_required_count - base.review_required_count
            ),
            display_only_delta=(
                result.counters.display_only_count - base.display_only_count
            ),
            blocked_delta=result.counters.blocked_count - base.blocked_count,
            source_attempt_delta=result.counters.source_attempt_count - base.source_attempt_count,
            successful_source_attempt_delta=(
                result.counters.successful_source_attempt_count
                - base.successful_source_attempt_count
            ),
            zero_yield_source_attempt_delta=(
                result.counters.zero_yield_source_attempt_count
                - base.zero_yield_source_attempt_count
            ),
            observation_yield_unit_delta=(
                result.counters.observation_yield_unit_count
                - base.observation_yield_unit_count
            ),
            request_cost_unit_delta=(
                result.counters.request_cost_unit_count - base.request_cost_unit_count
            ),
            labelled_admitted_pivot_delta=(
                result.counters.labelled_admitted_pivot_count
                - base.labelled_admitted_pivot_count
            ),
            wrong_pivot_delta=result.counters.wrong_pivot_count - base.wrong_pivot_count,
            relevant_pivot_delta=(
                result.counters.relevant_pivot_count - base.relevant_pivot_count
            ),
            unlabelled_admitted_pivot_delta=(
                result.counters.unlabelled_admitted_pivot_count
                - base.unlabelled_admitted_pivot_count
            ),
        )
        for result in candidate_results
    )
    return M10CohortComparison(
        baseline=baseline_result,
        candidates=candidate_results,
        deltas=deltas,
    )
