# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
    canonicalize_lead,
)
from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_evaluation import PivotRelevance
from app.intelligence.graph_limit_evaluation import GraphFixtureLead, GraphLimitScenario
from app.intelligence.m10_cohort import M10GraphFixture, compare_m10_graph_fixture_cohort


def _lead(value: str) -> LeadCandidate:
    display_value, comparison_key = canonicalize_lead(LeadKind.USERNAME, value)
    return LeadCandidate(
        kind=LeadKind.USERNAME,
        value=display_value,
        comparison_key=comparison_key,
        reason=LeadReason.PUBLIC_USERNAME,
        disposition=LeadDisposition.AUTO_PIVOT,
        source="m10_fixture",
        source_locator=f"fixture://{comparison_key}",
        field_name="public_username",
    )


def _fixtures() -> tuple[M10GraphFixture, ...]:
    depth_seed = _lead("depth-seed")
    alpha = _lead("alpha")
    beta = _lead("beta")
    deep_wrong = _lead("deep-wrong")

    duplicate_seed = _lead("duplicate-seed")
    repeated = _lead("repeated")

    failure_seed = _lead("failure-seed")
    failed = _lead("failed")
    kept = _lead("kept")

    return (
        M10GraphFixture(
            name="depth_tradeoff",
            seed_key=depth_seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent={
                depth_seed.key: (GraphFixtureLead(alpha),),
                alpha.key: (GraphFixtureLead(beta),),
                beta.key: (GraphFixtureLead(deep_wrong),),
            },
            pivot_relevance_by_key={
                alpha.key: PivotRelevance.RELEVANT,
                beta.key: PivotRelevance.RELEVANT,
                deep_wrong.key: PivotRelevance.WRONG,
            },
        ),
        M10GraphFixture(
            name="duplicate_heavy",
            seed_key=duplicate_seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent={
                duplicate_seed.key: (
                    GraphFixtureLead(repeated),
                    GraphFixtureLead(repeated),
                )
            },
            pivot_relevance_by_key={repeated.key: PivotRelevance.RELEVANT},
        ),
        M10GraphFixture(
            name="provider_failure",
            seed_key=failure_seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent={
                failure_seed.key: (
                    GraphFixtureLead(failed, provider_fails=True),
                    GraphFixtureLead(kept),
                )
            },
            pivot_relevance_by_key={kept.key: PivotRelevance.RELEVANT},
        ),
    )


def _scenario(name: str, *, depth: int) -> GraphLimitScenario:
    return GraphLimitScenario(
        name,
        compatibility_frontier_limits(max_depth=depth, max_nodes=12),
    )


def test_labelled_cohort_aggregates_independent_fixture_families() -> None:
    comparison = compare_m10_graph_fixture_cohort(
        fixtures=_fixtures(),
        baseline=_scenario("current_depth2_nodes12", depth=2),
        candidates=(_scenario("candidate_depth3_nodes12", depth=3),),
    )

    baseline = comparison.baseline.counters
    candidate = comparison.candidates[0].counters
    delta = comparison.deltas[0]

    assert baseline.fixture_count == 3
    assert baseline.node_count == 7
    assert baseline.added_node_count == 4
    assert baseline.max_observed_depth == 2
    assert baseline.duplicate_suppression_count == 1
    assert baseline.provider_failure_count == 1
    assert baseline.budget_stop_count == 1
    assert baseline.labelled_admitted_pivot_count == 4
    assert baseline.wrong_pivot_count == 0
    assert baseline.relevant_pivot_count == 4
    assert baseline.unlabelled_admitted_pivot_count == 0

    assert candidate.fixture_count == 3
    assert candidate.node_count == 8
    assert candidate.added_node_count == 5
    assert candidate.max_observed_depth == 3
    assert candidate.duplicate_suppression_count == 1
    assert candidate.provider_failure_count == 1
    assert candidate.budget_stop_count == 0
    assert candidate.labelled_admitted_pivot_count == 5
    assert candidate.wrong_pivot_count == 1
    assert candidate.relevant_pivot_count == 4
    assert candidate.unlabelled_admitted_pivot_count == 0

    assert delta.scenario_name == "candidate_depth3_nodes12"
    assert delta.node_delta == 1
    assert delta.added_node_delta == 1
    assert delta.max_observed_depth_delta == 1
    assert delta.duplicate_suppression_delta == 0
    assert delta.provider_failure_delta == 0
    assert delta.budget_stop_delta == -1
    assert delta.labelled_admitted_pivot_delta == 1
    assert delta.wrong_pivot_delta == 1
    assert delta.relevant_pivot_delta == 0
    assert delta.unlabelled_admitted_pivot_delta == 0


def test_cohort_requires_fixtures_and_unique_names() -> None:
    baseline = _scenario("current", depth=2)

    with pytest.raises(ValueError, match="at least one fixture"):
        compare_m10_graph_fixture_cohort(
            fixtures=(),
            baseline=baseline,
            candidates=(),
        )

    fixture = _fixtures()[0]
    with pytest.raises(ValueError, match="fixture names must be unique"):
        compare_m10_graph_fixture_cohort(
            fixtures=(fixture, fixture),
            baseline=baseline,
            candidates=(),
        )


def test_cohort_requires_unique_scenario_names() -> None:
    same = _scenario("same", depth=2)
    with pytest.raises(ValueError, match="scenario names must be unique"):
        compare_m10_graph_fixture_cohort(
            fixtures=_fixtures(),
            baseline=same,
            candidates=(same,),
        )


def test_cohort_preserves_underlying_fixture_truth_validation() -> None:
    seed = _lead("seed")
    child = _lead("child")
    fixture = M10GraphFixture(
        name="bad_truth",
        seed_key=seed.key,
        seed_kind=LeadKind.USERNAME,
        leads_by_parent={seed.key: (GraphFixtureLead(child),)},
        pivot_relevance_by_key={"username:missing": PivotRelevance.WRONG},
    )

    with pytest.raises(ValueError, match="possible successful result keys"):
        compare_m10_graph_fixture_cohort(
            fixtures=(fixture,),
            baseline=_scenario("current", depth=2),
            candidates=(),
        )
