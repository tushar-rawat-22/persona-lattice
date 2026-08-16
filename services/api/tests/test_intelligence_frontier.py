# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
)
from app.intelligence.frontier import FrontierDecision, FrontierLimits, LeadFrontier


def _candidate(
    kind: LeadKind,
    value: str,
    *,
    disposition: LeadDisposition = LeadDisposition.AUTO_PIVOT,
) -> LeadCandidate:
    return LeadCandidate(
        kind=kind,
        value=value,
        comparison_key=value,
        reason={
            LeadKind.USERNAME: LeadReason.PUBLIC_USERNAME,
            LeadKind.EMAIL: LeadReason.PUBLIC_EMAIL,
            LeadKind.PHONE: LeadReason.PUBLIC_PHONE,
            LeadKind.URL: LeadReason.PUBLIC_URL,
            LeadKind.DOMAIN: LeadReason.PUBLIC_DOMAIN,
            LeadKind.NAME: LeadReason.PUBLIC_NAME,
            LeadKind.ORGANIZATION: LeadReason.PUBLIC_ORGANIZATION,
            LeadKind.LOCATION: LeadReason.PUBLIC_LOCATION,
        }[kind],
        disposition=disposition,
        source="synthetic_public_source",
        source_locator="https://example.test/source",
        field_name="synthetic",
    )


def test_frontier_separates_review_display_and_automatic_leads() -> None:
    frontier = LeadFrontier(seed_key="username:seed", seed_kind=LeadKind.USERNAME)

    review = frontier.consider(
        _candidate(
            LeadKind.PHONE,
            "+919876543210",
            disposition=LeadDisposition.REVIEW_REQUIRED,
        ),
        parent_key="username:seed",
        parent_depth=0,
    )
    display = frontier.consider(
        _candidate(
            LeadKind.ORGANIZATION,
            "Example Corp",
            disposition=LeadDisposition.DISPLAY_ONLY,
        ),
        parent_key="username:seed",
        parent_depth=0,
    )
    auto = frontier.consider(
        _candidate(LeadKind.EMAIL, "person@example.test"),
        parent_key="username:seed",
        parent_depth=0,
    )

    assert review.decision is FrontierDecision.REVIEW_REQUIRED
    assert display.decision is FrontierDecision.DISPLAY_ONLY
    assert auto.decision is FrontierDecision.ENQUEUE
    assert frontier.reserved_count == 1


def test_frontier_reserves_candidate_before_provider_execution() -> None:
    frontier = LeadFrontier(seed_key="username:seed", seed_kind=LeadKind.USERNAME)
    candidate = _candidate(LeadKind.EMAIL, "person@example.test")

    first = frontier.consider(candidate, parent_key="username:seed", parent_depth=0)
    second = frontier.consider(candidate, parent_key="username:seed", parent_depth=0)

    assert first.decision is FrontierDecision.ENQUEUE
    assert second.decision is FrontierDecision.DUPLICATE
    assert frontier.node_count == 1
    assert frontier.edge_count == 0
    assert frontier.reserved_count == 1


def test_frontier_counts_outstanding_reservations_against_node_budget() -> None:
    frontier = LeadFrontier(
        seed_key="username:seed",
        seed_kind=LeadKind.USERNAME,
        limits=FrontierLimits(max_nodes=2),
    )
    first = _candidate(LeadKind.EMAIL, "one@example.test")
    second = _candidate(LeadKind.URL, "https://two.example.test")

    assert (
        frontier.consider(first, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.ENQUEUE
    )
    assert frontier.reserved_count == 1
    assert (
        frontier.consider(second, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.NODE_LIMIT
    )


def test_frontier_counts_outstanding_reservations_against_kind_and_parent_budgets() -> None:
    frontier = LeadFrontier(
        seed_key="username:seed",
        seed_kind=LeadKind.USERNAME,
        limits=FrontierLimits(max_email_nodes=1, max_auto_children_per_parent=1),
    )
    first = _candidate(LeadKind.EMAIL, "one@example.test")
    second_email = _candidate(LeadKind.EMAIL, "two@example.test")
    second_url = _candidate(LeadKind.URL, "https://two.example.test")

    assert (
        frontier.consider(first, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.ENQUEUE
    )
    assert (
        frontier.consider(second_email, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.PARENT_FANOUT_LIMIT
    )
    assert (
        frontier.consider(second_url, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.PARENT_FANOUT_LIMIT
    )


def test_frontier_fail_releases_capacity_but_does_not_retry_same_lead() -> None:
    frontier = LeadFrontier(
        seed_key="username:seed",
        seed_kind=LeadKind.USERNAME,
        limits=FrontierLimits(max_nodes=2),
    )
    first = _candidate(LeadKind.EMAIL, "one@example.test")
    second = _candidate(LeadKind.URL, "https://two.example.test")

    assert (
        frontier.consider(first, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.ENQUEUE
    )
    frontier.fail(first)
    assert frontier.reserved_count == 0
    assert (
        frontier.consider(first, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.DUPLICATE
    )
    assert (
        frontier.consider(second, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.ENQUEUE
    )


def test_frontier_enforces_depth_node_edge_kind_and_parent_limits() -> None:
    depth_frontier = LeadFrontier(
        seed_key="username:seed",
        seed_kind=LeadKind.USERNAME,
        limits=FrontierLimits(max_depth=0),
    )
    assert (
        depth_frontier.consider(
            _candidate(LeadKind.EMAIL, "a@example.test"),
            parent_key="username:seed",
            parent_depth=0,
        ).decision
        is FrontierDecision.DEPTH_LIMIT
    )

    node_frontier = LeadFrontier(
        seed_key="username:seed",
        seed_kind=LeadKind.USERNAME,
        limits=FrontierLimits(max_nodes=1),
    )
    assert (
        node_frontier.consider(
            _candidate(LeadKind.EMAIL, "a@example.test"),
            parent_key="username:seed",
            parent_depth=0,
        ).decision
        is FrontierDecision.NODE_LIMIT
    )

    edge_frontier = LeadFrontier(
        seed_key="username:seed",
        seed_kind=LeadKind.USERNAME,
        limits=FrontierLimits(max_edges=0),
    )
    assert (
        edge_frontier.consider(
            _candidate(LeadKind.EMAIL, "a@example.test"),
            parent_key="username:seed",
            parent_depth=0,
        ).decision
        is FrontierDecision.EDGE_LIMIT
    )

    kind_frontier = LeadFrontier(
        seed_key="email:seed@example.test",
        seed_kind=LeadKind.EMAIL,
        limits=FrontierLimits(max_email_nodes=1),
    )
    assert (
        kind_frontier.consider(
            _candidate(LeadKind.EMAIL, "other@example.test"),
            parent_key="email:seed@example.test",
            parent_depth=0,
        ).decision
        is FrontierDecision.KIND_LIMIT
    )

    fanout_frontier = LeadFrontier(
        seed_key="username:seed",
        seed_kind=LeadKind.USERNAME,
        limits=FrontierLimits(max_auto_children_per_parent=1),
    )
    first = _candidate(LeadKind.EMAIL, "one@example.test")
    assert (
        fanout_frontier.consider(first, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.ENQUEUE
    )
    assert (
        fanout_frontier.admit(
            first,
            actual_key=first.key,
            parent_key="username:seed",
        )
        is FrontierDecision.ENQUEUE
    )
    second = _candidate(LeadKind.URL, "https://example.test")
    assert (
        fanout_frontier.consider(second, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.PARENT_FANOUT_LIMIT
    )


def test_frontier_admit_requires_matching_reservation_parent() -> None:
    frontier = LeadFrontier(seed_key="username:seed", seed_kind=LeadKind.USERNAME)
    candidate = _candidate(LeadKind.EMAIL, "person@example.test")

    assert (
        frontier.consider(candidate, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.ENQUEUE
    )
    with pytest.raises(ValueError, match="parent"):
        frontier.admit(
            candidate,
            actual_key=candidate.key,
            parent_key="username:other",
        )
    assert frontier.reserved_count == 0


def test_frontier_admit_suppresses_provider_normalized_duplicates() -> None:
    frontier = LeadFrontier(seed_key="username:seed", seed_kind=LeadKind.USERNAME)
    first = _candidate(LeadKind.URL, "https://example.test/profile")
    second = _candidate(LeadKind.URL, "https://example.test/profile#duplicate")

    assert (
        frontier.consider(first, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.ENQUEUE
    )
    assert (
        frontier.admit(
            first,
            actual_key="url:https://example.test/profile",
            parent_key="username:seed",
        )
        is FrontierDecision.ENQUEUE
    )

    assert (
        frontier.consider(second, parent_key="username:seed", parent_depth=0).decision
        is FrontierDecision.ENQUEUE
    )
    assert (
        frontier.admit(
            second,
            actual_key="url:https://example.test/profile",
            parent_key="username:seed",
        )
        is FrontierDecision.DUPLICATE
    )
    assert frontier.node_count == 2
    assert frontier.edge_count == 1
    assert frontier.reserved_count == 0
