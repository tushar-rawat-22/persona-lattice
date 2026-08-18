# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .contracts import LeadKind
from .graph_evaluation import PivotRelevance
from .graph_limit_evaluation import (
    GraphFixtureLead,
    GraphLimitScenario,
    evaluate_graph_limit_fixture,
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
        evaluate_graph_limit_fixture(
            seed_key=fixture.seed_key,
            seed_kind=fixture.seed_kind,
            leads_by_parent=fixture.leads_by_parent,
            pivot_relevance_by_key=fixture.pivot_relevance_by_key,
            limits=scenario.limits,
        )
        for fixture in fixtures
    )
    return M10CohortScenarioResult(
        scenario=scenario,
        counters=M10CohortCounters(
            fixture_count=len(results),
            node_count=sum(item.node_count for item in results),
            added_node_count=sum(item.added_node_count for item in results),
            max_observed_depth=max(item.max_observed_depth for item in results),
            duplicate_suppression_count=sum(
                item.duplicate_suppression_count for item in results
            ),
            provider_failure_count=sum(item.provider_failure_count for item in results),
            budget_stop_count=sum(item.budget_stop_count for item in results),
            labelled_admitted_pivot_count=sum(
                item.labelled_admitted_pivot_count for item in results
            ),
            wrong_pivot_count=sum(item.wrong_pivot_count for item in results),
            relevant_pivot_count=sum(item.relevant_pivot_count for item in results),
            unlabelled_admitted_pivot_count=sum(
                item.unlabelled_admitted_pivot_count for item in results
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
    calculate reliability percentages, or convert labels into identity probability.
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
