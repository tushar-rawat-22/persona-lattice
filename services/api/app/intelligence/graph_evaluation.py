# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .frontier import FrontierDecision


class PivotRelevance(StrEnum):
    """Fixture/operator label for whether an admitted pivot belongs in the research graph.

    This is an evaluation label, not an identity claim. Production runtime behavior
    must never infer it from usernames, provider agreement, M5 output or graph shape.
    """

    RELEVANT = "relevant"
    WRONG = "wrong"


class _NodeLike(Protocol):
    depth: int


class _LeadDecisionLike(Protocol):
    decision: FrontierDecision
    child_key: str | None


class _GraphReportLike(Protocol):
    nodes: Sequence[_NodeLike]
    edges: Sequence[object]
    lead_decisions: Sequence[_LeadDecisionLike]
    truncated: bool


@dataclass(frozen=True, slots=True)
class GraphEvaluationCounters:
    """Deterministic descriptive counters for bounded recursive graph behavior."""

    node_count: int
    added_node_count: int
    edge_count: int
    max_observed_depth: int
    lead_decision_count: int
    automatic_terminal_decision_count: int
    admitted_pivot_count: int
    duplicate_suppression_count: int
    provider_failure_count: int
    budget_stop_count: int
    review_required_count: int
    display_only_count: int
    blocked_count: int
    truncated: bool
    labelled_admitted_pivot_count: int
    wrong_pivot_count: int
    relevant_pivot_count: int
    unlabelled_admitted_pivot_count: int

    @property
    def wrong_pivot_denominator(self) -> int:
        """Return the only valid denominator for a labelled wrong-pivot rate."""

        return self.labelled_admitted_pivot_count

    @property
    def duplicate_suppression_denominator(self) -> int:
        """Return terminal automatic lead decisions considered for duplicate share."""

        return self.automatic_terminal_decision_count


_BUDGET_STOPS = frozenset(
    {
        FrontierDecision.DEPTH_LIMIT,
        FrontierDecision.NODE_LIMIT,
        FrontierDecision.EDGE_LIMIT,
        FrontierDecision.KIND_LIMIT,
        FrontierDecision.PARENT_FANOUT_LIMIT,
    }
)
_AUTOMATIC_TERMINAL = frozenset(
    {
        FrontierDecision.ADMITTED,
        FrontierDecision.PROVIDER_FAILED,
        FrontierDecision.DUPLICATE,
        *_BUDGET_STOPS,
    }
)


def build_graph_evaluation_counters(
    report: _GraphReportLike,
    *,
    admitted_pivot_labels: Mapping[str, PivotRelevance] | None = None,
) -> GraphEvaluationCounters:
    """Measure graph growth and labelled pivot quality without inferring ground truth.

    `admitted_pivot_labels` is intentionally keyed by admitted child node key. Labels
    must come from deterministic synthetic fixtures or explicit consented evaluation
    truth. An unknown/non-admitted key is rejected so a caller cannot accidentally
    score a lead that the graph never admitted.
    """

    labels = dict(admitted_pivot_labels or {})
    decision_counts = Counter(record.decision for record in report.lead_decisions)
    admitted_keys = {
        record.child_key
        for record in report.lead_decisions
        if record.decision is FrontierDecision.ADMITTED and record.child_key is not None
    }
    invalid_label_keys = sorted(set(labels) - admitted_keys)
    if invalid_label_keys:
        raise ValueError(
            "Graph evaluation labels must reference admitted child keys only: "
            f"invalid={invalid_label_keys!r}."
        )

    invalid_label_values = sorted(
        key for key, label in labels.items() if not isinstance(label, PivotRelevance)
    )
    if invalid_label_values:
        raise TypeError(
            "Graph evaluation labels must use PivotRelevance values: "
            f"invalid={invalid_label_values!r}."
        )

    wrong_pivot_count = sum(label is PivotRelevance.WRONG for label in labels.values())
    relevant_pivot_count = sum(label is PivotRelevance.RELEVANT for label in labels.values())
    admitted_pivot_count = decision_counts[FrontierDecision.ADMITTED]
    automatic_terminal_decision_count = sum(
        decision_counts[decision] for decision in _AUTOMATIC_TERMINAL
    )

    node_count = len(report.nodes)
    return GraphEvaluationCounters(
        node_count=node_count,
        added_node_count=max(0, node_count - 1),
        edge_count=len(report.edges),
        max_observed_depth=max((node.depth for node in report.nodes), default=0),
        lead_decision_count=len(report.lead_decisions),
        automatic_terminal_decision_count=automatic_terminal_decision_count,
        admitted_pivot_count=admitted_pivot_count,
        duplicate_suppression_count=decision_counts[FrontierDecision.DUPLICATE],
        provider_failure_count=decision_counts[FrontierDecision.PROVIDER_FAILED],
        budget_stop_count=sum(decision_counts[decision] for decision in _BUDGET_STOPS),
        review_required_count=decision_counts[FrontierDecision.REVIEW_REQUIRED],
        display_only_count=decision_counts[FrontierDecision.DISPLAY_ONLY],
        blocked_count=decision_counts[FrontierDecision.BLOCKED],
        truncated=bool(report.truncated),
        labelled_admitted_pivot_count=len(labels),
        wrong_pivot_count=wrong_pivot_count,
        relevant_pivot_count=relevant_pivot_count,
        unlabelled_admitted_pivot_count=admitted_pivot_count - len(labels),
    )
