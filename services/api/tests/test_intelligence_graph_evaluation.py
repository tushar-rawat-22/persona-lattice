# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.intelligence.frontier import FrontierDecision
from app.intelligence.graph_evaluation import (
    PivotRelevance,
    build_graph_evaluation_counters,
)


@dataclass(frozen=True)
class _Node:
    depth: int


@dataclass(frozen=True)
class _Decision:
    decision: FrontierDecision
    child_key: str | None = None


@dataclass(frozen=True)
class _Report:
    nodes: tuple[_Node, ...]
    edges: tuple[object, ...]
    lead_decisions: tuple[_Decision, ...]
    truncated: bool


def _fixture_report() -> _Report:
    return _Report(
        nodes=(_Node(0), _Node(1), _Node(1), _Node(2)),
        edges=(object(), object(), object()),
        lead_decisions=(
            _Decision(FrontierDecision.ADMITTED, "username:alpha"),
            _Decision(FrontierDecision.DUPLICATE),
            _Decision(FrontierDecision.PROVIDER_FAILED),
            _Decision(FrontierDecision.ADMITTED, "email:wrong@example.test"),
            _Decision(FrontierDecision.DEPTH_LIMIT),
            _Decision(FrontierDecision.REVIEW_REQUIRED),
            _Decision(FrontierDecision.DISPLAY_ONLY),
            _Decision(FrontierDecision.BLOCKED),
        ),
        truncated=True,
    )


def test_graph_evaluation_counts_growth_duplicates_and_labelled_wrong_pivots() -> None:
    counters = build_graph_evaluation_counters(
        _fixture_report(),
        admitted_pivot_labels={
            "username:alpha": PivotRelevance.RELEVANT,
            "email:wrong@example.test": PivotRelevance.WRONG,
        },
    )

    assert counters.node_count == 4
    assert counters.added_node_count == 3
    assert counters.edge_count == 3
    assert counters.max_observed_depth == 2
    assert counters.lead_decision_count == 8
    assert counters.automatic_terminal_decision_count == 5
    assert counters.admitted_pivot_count == 2
    assert counters.duplicate_suppression_count == 1
    assert counters.provider_failure_count == 1
    assert counters.budget_stop_count == 1
    assert counters.review_required_count == 1
    assert counters.display_only_count == 1
    assert counters.blocked_count == 1
    assert counters.truncated is True
    assert counters.labelled_admitted_pivot_count == 2
    assert counters.wrong_pivot_denominator == 2
    assert counters.wrong_pivot_count == 1
    assert counters.relevant_pivot_count == 1
    assert counters.unlabelled_admitted_pivot_count == 0
    assert counters.duplicate_suppression_denominator == 5


def test_wrong_pivot_measurement_never_infers_truth_for_unlabelled_admissions() -> None:
    counters = build_graph_evaluation_counters(_fixture_report())

    assert counters.admitted_pivot_count == 2
    assert counters.labelled_admitted_pivot_count == 0
    assert counters.wrong_pivot_denominator == 0
    assert counters.wrong_pivot_count == 0
    assert counters.relevant_pivot_count == 0
    assert counters.unlabelled_admitted_pivot_count == 2


def test_labels_must_reference_admitted_child_nodes() -> None:
    with pytest.raises(ValueError, match="admitted child keys only"):
        build_graph_evaluation_counters(
            _fixture_report(),
            admitted_pivot_labels={"username:not-admitted": PivotRelevance.WRONG},
        )


def test_labels_require_explicit_pivot_relevance_values() -> None:
    with pytest.raises(TypeError, match="PivotRelevance"):
        build_graph_evaluation_counters(
            _fixture_report(),
            admitted_pivot_labels={"username:alpha": "relevant"},  # type: ignore[dict-item]
        )


def test_graph_evaluation_is_order_invariant() -> None:
    report = _fixture_report()
    reversed_report = _Report(
        nodes=tuple(reversed(report.nodes)),
        edges=tuple(reversed(report.edges)),
        lead_decisions=tuple(reversed(report.lead_decisions)),
        truncated=report.truncated,
    )
    labels = {
        "username:alpha": PivotRelevance.RELEVANT,
        "email:wrong@example.test": PivotRelevance.WRONG,
    }

    assert build_graph_evaluation_counters(
        report, admitted_pivot_labels=labels
    ) == build_graph_evaluation_counters(
        reversed_report, admitted_pivot_labels=labels
    )
