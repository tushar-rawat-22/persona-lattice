# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
    canonicalize_lead,
)
from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_limit_evaluation import (
    GraphFixtureLead,
    evaluate_graph_limit_fixture_with_operations,
)


def _username(value: str) -> LeadCandidate:
    display_value, comparison_key = canonicalize_lead(LeadKind.USERNAME, value)
    return LeadCandidate(
        kind=LeadKind.USERNAME,
        value=display_value,
        comparison_key=comparison_key,
        reason=LeadReason.PUBLIC_USERNAME,
        disposition=LeadDisposition.AUTO_PIVOT,
        source="m10_fixture",
        source_locator=f"fixture://username/{comparison_key}",
        field_name=LeadReason.PUBLIC_USERNAME.value,
    )


def test_successful_call_counts_cost_and_yield_even_if_returned_key_is_duplicate() -> None:
    seed = _username("seed")
    candidate = _username("candidate")

    evaluation = evaluate_graph_limit_fixture_with_operations(
        seed_key=seed.key,
        seed_kind=LeadKind.USERNAME,
        leads_by_parent={
            seed.key: (GraphFixtureLead(candidate, actual_key=seed.key),),
        },
        pivot_relevance_by_key={},
        limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
    )

    assert evaluation.graph.added_node_count == 0
    assert evaluation.graph.duplicate_suppression_count == 1
    assert evaluation.operational.source_attempt_count == 1
    assert evaluation.operational.successful_source_attempt_count == 1
    assert evaluation.operational.zero_yield_source_attempt_count == 0
    assert evaluation.operational.observation_yield_unit_count == 1
    assert evaluation.operational.request_cost_unit_count == 1


def test_pre_call_duplicate_and_review_only_leads_consume_no_request_cost() -> None:
    seed = _username("seed")
    duplicate = _username("seed")
    review_display, review_key = canonicalize_lead(LeadKind.PHONE, "+14155552671")
    review = LeadCandidate(
        kind=LeadKind.PHONE,
        value=review_display,
        comparison_key=review_key,
        reason=LeadReason.PUBLIC_PHONE,
        disposition=LeadDisposition.REVIEW_REQUIRED,
        source="m10_fixture",
        source_locator="fixture://phone/review",
        field_name=LeadReason.PUBLIC_PHONE.value,
    )

    evaluation = evaluate_graph_limit_fixture_with_operations(
        seed_key=seed.key,
        seed_kind=LeadKind.USERNAME,
        leads_by_parent={
            seed.key: (GraphFixtureLead(duplicate), GraphFixtureLead(review)),
        },
        pivot_relevance_by_key={},
        limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
    )

    assert evaluation.graph.duplicate_suppression_count == 1
    assert evaluation.graph.review_required_count == 1
    assert evaluation.operational.source_attempt_count == 0
    assert evaluation.operational.observation_yield_unit_count == 0
    assert evaluation.operational.request_cost_unit_count == 0
