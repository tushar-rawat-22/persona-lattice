# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.convergence import _compatibility_frontier_limits
from app.intelligence.contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
    canonicalize_lead,
)
from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_evaluation import PivotRelevance
from app.intelligence.graph_limit_evaluation import (
    GraphFixtureLead,
    GraphLimitScenario,
    compare_graph_limit_fixture,
    evaluate_graph_limit_fixture,
)


def _lead(value: str) -> LeadCandidate:
    display_value, comparison_key = canonicalize_lead(LeadKind.USERNAME, value)
    return LeadCandidate(
        kind=LeadKind.USERNAME,
        value=display_value,
        comparison_key=comparison_key,
        reason=LeadReason.PUBLIC_USERNAME,
        disposition=LeadDisposition.AUTO_PIVOT,
        source="synthetic_graph_fixture",
        source_locator=f"fixture://{comparison_key}",
        field_name="public_username",
    )


def _labelled_fixture() -> tuple[
    str,
    dict[str, tuple[GraphFixtureLead, ...]],
    dict[str, PivotRelevance],
]:
    seed_key = _lead("seed").key
    alpha = _lead("alpha")
    wrong_one = _lead("wrong-one")
    beta = _lead("beta")
    wrong_two = _lead("wrong-two")
    wrong_three = _lead("wrong-three")
    deep_good = _lead("deep-good")
    deep_wrong = _lead("deep-wrong")

    leads_by_parent = {
        seed_key: (GraphFixtureLead(alpha), GraphFixtureLead(wrong_one)),
        alpha.key: (GraphFixtureLead(beta), GraphFixtureLead(wrong_two)),
        wrong_one.key: (GraphFixtureLead(beta), GraphFixtureLead(wrong_three)),
        beta.key: (GraphFixtureLead(deep_good),),
        wrong_two.key: (GraphFixtureLead(deep_wrong),),
        wrong_three.key: (GraphFixtureLead(deep_good),),
    }
    truth = {
        alpha.key: PivotRelevance.RELEVANT,
        wrong_one.key: PivotRelevance.WRONG,
        beta.key: PivotRelevance.RELEVANT,
        wrong_two.key: PivotRelevance.WRONG,
        wrong_three.key: PivotRelevance.WRONG,
        deep_good.key: PivotRelevance.RELEVANT,
        deep_wrong.key: PivotRelevance.WRONG,
    }
    return seed_key, leads_by_parent, truth


def test_shared_compatibility_limits_match_current_production_policy() -> None:
    assert compatibility_frontier_limits(
        max_depth=2,
        max_nodes=12,
    ) == _compatibility_frontier_limits(max_depth=2, max_nodes=12)


def test_labelled_fixture_exposes_capacity_tradeoffs_without_changing_production_limits() -> None:
    seed_key, leads_by_parent, truth = _labelled_fixture()
    comparison = compare_graph_limit_fixture(
        seed_key=seed_key,
        seed_kind=LeadKind.USERNAME,
        leads_by_parent=leads_by_parent,
        pivot_relevance_by_key=truth,
        baseline=GraphLimitScenario(
            "current_depth2_nodes12",
            compatibility_frontier_limits(max_depth=2, max_nodes=12),
        ),
        candidates=(
            GraphLimitScenario(
                "candidate_depth3_nodes12",
                compatibility_frontier_limits(max_depth=3, max_nodes=12),
            ),
        ),
    )

    baseline = comparison.baseline.counters
    candidate = comparison.candidates[0].counters
    delta = comparison.deltas[0]

    assert baseline.node_count == 6
    assert baseline.added_node_count == 5
    assert baseline.max_observed_depth == 2
    assert baseline.duplicate_suppression_count == 1
    assert baseline.budget_stop_count == 3
    assert baseline.labelled_admitted_pivot_count == 5
    assert baseline.wrong_pivot_denominator == 5
    assert baseline.wrong_pivot_count == 3
    assert baseline.relevant_pivot_count == 2
    assert baseline.truncated is True

    assert candidate.node_count == 8
    assert candidate.added_node_count == 7
    assert candidate.max_observed_depth == 3
    assert candidate.duplicate_suppression_count == 2
    assert candidate.budget_stop_count == 0
    assert candidate.labelled_admitted_pivot_count == 7
    assert candidate.wrong_pivot_denominator == 7
    assert candidate.wrong_pivot_count == 4
    assert candidate.relevant_pivot_count == 3
    assert candidate.truncated is False

    assert delta.scenario_name == "candidate_depth3_nodes12"
    assert delta.added_node_delta == 2
    assert delta.max_observed_depth_delta == 1
    assert delta.duplicate_suppression_delta == 1
    assert delta.budget_stop_delta == -3
    assert delta.labelled_admitted_pivot_delta == 2
    assert delta.wrong_pivot_delta == 1
    assert delta.relevant_pivot_delta == 1
    assert delta.unlabelled_admitted_pivot_delta == 0


def test_fixture_provider_failures_release_capacity_without_becoming_pivot_labels() -> None:
    seed = _lead("seed")
    failed = _lead("failed")
    admitted = _lead("admitted")
    counters = evaluate_graph_limit_fixture(
        seed_key=seed.key,
        seed_kind=LeadKind.USERNAME,
        leads_by_parent={
            seed.key: (
                GraphFixtureLead(failed, provider_fails=True),
                GraphFixtureLead(admitted),
            )
        },
        pivot_relevance_by_key={admitted.key: PivotRelevance.RELEVANT},
        limits=compatibility_frontier_limits(max_depth=2, max_nodes=2),
    )

    assert counters.node_count == 2
    assert counters.provider_failure_count == 1
    assert counters.admitted_pivot_count == 1
    assert counters.relevant_pivot_count == 1
    assert counters.wrong_pivot_count == 0


def test_fixture_truth_rejects_unknown_keys_and_non_enum_labels() -> None:
    seed = _lead("seed")
    child = _lead("child")
    leads = {seed.key: (GraphFixtureLead(child),)}

    with pytest.raises(ValueError, match="possible successful result keys"):
        evaluate_graph_limit_fixture(
            seed_key=seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent=leads,
            pivot_relevance_by_key={"username:missing": PivotRelevance.WRONG},
            limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
        )

    with pytest.raises(TypeError, match="PivotRelevance"):
        evaluate_graph_limit_fixture(
            seed_key=seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent=leads,
            pivot_relevance_by_key={child.key: "relevant"},  # type: ignore[dict-item]
            limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
        )


def test_limit_comparison_rejects_duplicate_scenario_names() -> None:
    seed_key, leads_by_parent, truth = _labelled_fixture()
    scenario = GraphLimitScenario(
        "same_name",
        compatibility_frontier_limits(max_depth=2, max_nodes=12),
    )

    with pytest.raises(ValueError, match="scenario names must be unique"):
        compare_graph_limit_fixture(
            seed_key=seed_key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent=leads_by_parent,
            pivot_relevance_by_key=truth,
            baseline=scenario,
            candidates=(scenario,),
        )
