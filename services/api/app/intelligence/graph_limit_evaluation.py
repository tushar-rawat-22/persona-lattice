# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .contracts import LeadCandidate, LeadDisposition, LeadKind
from .frontier import FrontierDecision, FrontierLimits, LeadFrontier
from .graph_evaluation import (
    GraphEvaluationCounters,
    PivotRelevance,
    build_graph_evaluation_counters,
)


_BUDGET_STOPS = frozenset(
    {
        FrontierDecision.DEPTH_LIMIT,
        FrontierDecision.NODE_LIMIT,
        FrontierDecision.EDGE_LIMIT,
        FrontierDecision.KIND_LIMIT,
        FrontierDecision.PARENT_FANOUT_LIMIT,
    }
)


@dataclass(frozen=True, slots=True)
class GraphFixtureLead:
    """One deterministic lead emitted by a synthetic/consented fixture parent."""

    candidate: LeadCandidate
    provider_fails: bool = False
    actual_key: str | None = None

    def __post_init__(self) -> None:
        if self.provider_fails and self.candidate.disposition is not LeadDisposition.AUTO_PIVOT:
            raise ValueError("Only automatic fixture leads can model a provider failure.")
        if self.provider_fails and self.actual_key is not None:
            raise ValueError("A failed fixture provider cannot also declare an admitted result key.")
        if self.actual_key is not None and (
            not self.actual_key or self.actual_key.strip() != self.actual_key
        ):
            raise ValueError("Fixture actual_key must be non-empty and trimmed when provided.")
        if (
            self.actual_key is not None
            and self.candidate.disposition is not LeadDisposition.AUTO_PIVOT
        ):
            raise ValueError("Only automatic fixture leads may declare an actual result key.")
        if self.actual_key is not None:
            expected_prefix = f"{self.candidate.kind.value}:"
            if not self.actual_key.startswith(expected_prefix) or not self.actual_key[len(expected_prefix) :]:
                raise ValueError("Fixture actual_key kind must match the candidate lead kind.")

    @property
    def result_key(self) -> str:
        return self.actual_key or self.candidate.key


@dataclass(frozen=True, slots=True)
class GraphLimitScenario:
    """Named frontier limits used only for deterministic comparison."""

    name: str
    limits: FrontierLimits

    def __post_init__(self) -> None:
        if not self.name or self.name.strip() != self.name:
            raise ValueError("Graph limit scenario name must be non-empty and trimmed.")


@dataclass(frozen=True, slots=True)
class GraphLimitScenarioResult:
    scenario: GraphLimitScenario
    counters: GraphEvaluationCounters


@dataclass(frozen=True, slots=True)
class GraphLimitDelta:
    """Count-only change from the baseline; no quality/rate inference is made."""

    scenario_name: str
    added_node_delta: int
    max_observed_depth_delta: int
    duplicate_suppression_delta: int
    budget_stop_delta: int
    labelled_admitted_pivot_delta: int
    wrong_pivot_delta: int
    relevant_pivot_delta: int
    unlabelled_admitted_pivot_delta: int


@dataclass(frozen=True, slots=True)
class GraphLimitComparison:
    baseline: GraphLimitScenarioResult
    candidates: tuple[GraphLimitScenarioResult, ...]
    deltas: tuple[GraphLimitDelta, ...]


@dataclass(frozen=True, slots=True)
class _FixtureNode:
    key: str
    depth: int


@dataclass(frozen=True, slots=True)
class _FixtureDecision:
    decision: FrontierDecision
    child_key: str | None = None


@dataclass(frozen=True, slots=True)
class _FixtureReport:
    nodes: tuple[_FixtureNode, ...]
    edges: tuple[tuple[str, str], ...]
    lead_decisions: tuple[_FixtureDecision, ...]
    truncated: bool


def _validate_fixture_truth(
    *,
    seed_key: str,
    seed_kind: LeadKind,
    leads_by_parent: Mapping[str, Sequence[GraphFixtureLead]],
    pivot_relevance_by_key: Mapping[str, PivotRelevance],
) -> None:
    if not seed_key or seed_key.strip() != seed_key:
        raise ValueError("Fixture seed_key must be non-empty and trimmed.")
    seed_prefix = f"{seed_kind.value}:"
    if not seed_key.startswith(seed_prefix) or not seed_key[len(seed_prefix) :]:
        raise ValueError("Fixture seed_key kind must match seed_kind.")

    possible_result_keys = {
        lead.result_key
        for leads in leads_by_parent.values()
        for lead in leads
        if lead.candidate.disposition is LeadDisposition.AUTO_PIVOT and not lead.provider_fails
    }
    invalid_parent_keys = sorted(set(leads_by_parent) - ({seed_key} | possible_result_keys))
    if invalid_parent_keys:
        raise ValueError(
            "Fixture parent keys must be the seed or possible successful result keys: "
            f"invalid={invalid_parent_keys!r}."
        )

    invalid_keys = sorted(set(pivot_relevance_by_key) - possible_result_keys)
    if invalid_keys:
        raise ValueError(
            "Fixture pivot labels must reference possible successful result keys: "
            f"invalid={invalid_keys!r}."
        )
    if seed_key in pivot_relevance_by_key:
        raise ValueError("The seed is not an admitted pivot and cannot receive a pivot label.")

    invalid_values = sorted(
        key
        for key, label in pivot_relevance_by_key.items()
        if not isinstance(label, PivotRelevance)
    )
    if invalid_values:
        raise TypeError(
            "Fixture pivot labels must use PivotRelevance values: "
            f"invalid={invalid_values!r}."
        )


def evaluate_graph_limit_fixture(
    *,
    seed_key: str,
    seed_kind: LeadKind,
    leads_by_parent: Mapping[str, Sequence[GraphFixtureLead]],
    pivot_relevance_by_key: Mapping[str, PivotRelevance],
    limits: FrontierLimits,
) -> GraphEvaluationCounters:
    """Run one network-free fixture through the real LeadFrontier policy.

    The fixture supplies only deterministic lead emissions, provider success/failure
    facts and optional external relevance labels. It does not call research providers,
    infer identity truth or change production convergence limits.
    """

    _validate_fixture_truth(
        seed_key=seed_key,
        seed_kind=seed_kind,
        leads_by_parent=leads_by_parent,
        pivot_relevance_by_key=pivot_relevance_by_key,
    )

    frontier = LeadFrontier(seed_key=seed_key, seed_kind=seed_kind, limits=limits)
    depths = {seed_key: 0}
    queue: deque[str] = deque([seed_key])
    nodes: list[_FixtureNode] = [_FixtureNode(seed_key, 0)]
    edges: list[tuple[str, str]] = []
    decisions: list[_FixtureDecision] = []
    admitted_keys: set[str] = set()
    truncated = False

    while queue:
        parent_key = queue.popleft()
        parent_depth = depths[parent_key]
        for fixture_lead in leads_by_parent.get(parent_key, ()):
            candidate = fixture_lead.candidate
            evaluation = frontier.consider(
                candidate,
                parent_key=parent_key,
                parent_depth=parent_depth,
            )
            if evaluation.decision is not FrontierDecision.ENQUEUE:
                decisions.append(_FixtureDecision(evaluation.decision))
                if evaluation.decision in _BUDGET_STOPS:
                    truncated = True
                continue

            if fixture_lead.provider_fails:
                decisions.append(_FixtureDecision(frontier.fail(candidate)))
                continue

            child_key = fixture_lead.result_key
            admission = frontier.admit(
                candidate,
                actual_key=child_key,
                parent_key=parent_key,
            )
            decisions.append(_FixtureDecision(admission, child_key))
            if admission in _BUDGET_STOPS:
                truncated = True
            if admission is not FrontierDecision.ADMITTED:
                continue

            child_depth = parent_depth + 1
            depths[child_key] = child_depth
            nodes.append(_FixtureNode(child_key, child_depth))
            edges.append((parent_key, child_key))
            admitted_keys.add(child_key)
            queue.append(child_key)

    admitted_labels = {
        key: label for key, label in pivot_relevance_by_key.items() if key in admitted_keys
    }
    return build_graph_evaluation_counters(
        _FixtureReport(
            nodes=tuple(nodes),
            edges=tuple(edges),
            lead_decisions=tuple(decisions),
            truncated=truncated,
        ),
        admitted_pivot_labels=admitted_labels,
    )


def compare_graph_limit_fixture(
    *,
    seed_key: str,
    seed_kind: LeadKind,
    leads_by_parent: Mapping[str, Sequence[GraphFixtureLead]],
    pivot_relevance_by_key: Mapping[str, PivotRelevance],
    baseline: GraphLimitScenario,
    candidates: Sequence[GraphLimitScenario],
) -> GraphLimitComparison:
    """Compare candidate frontier policies against one named baseline fixture run."""

    candidate_tuple = tuple(candidates)
    names = [baseline.name, *(scenario.name for scenario in candidate_tuple)]
    if len(set(names)) != len(names):
        raise ValueError("Graph limit comparison scenario names must be unique.")

    def run(scenario: GraphLimitScenario) -> GraphLimitScenarioResult:
        return GraphLimitScenarioResult(
            scenario=scenario,
            counters=evaluate_graph_limit_fixture(
                seed_key=seed_key,
                seed_kind=seed_kind,
                leads_by_parent=leads_by_parent,
                pivot_relevance_by_key=pivot_relevance_by_key,
                limits=scenario.limits,
            ),
        )

    baseline_result = run(baseline)
    candidate_results = tuple(run(scenario) for scenario in candidate_tuple)
    base = baseline_result.counters
    deltas = tuple(
        GraphLimitDelta(
            scenario_name=result.scenario.name,
            added_node_delta=result.counters.added_node_count - base.added_node_count,
            max_observed_depth_delta=(
                result.counters.max_observed_depth - base.max_observed_depth
            ),
            duplicate_suppression_delta=(
                result.counters.duplicate_suppression_count
                - base.duplicate_suppression_count
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
    return GraphLimitComparison(
        baseline=baseline_result,
        candidates=candidate_results,
        deltas=deltas,
    )
