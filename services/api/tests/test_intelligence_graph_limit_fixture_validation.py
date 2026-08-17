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
from app.intelligence.graph_limit_evaluation import GraphFixtureLead, evaluate_graph_limit_fixture


def _username_lead(value: str) -> LeadCandidate:
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


def test_fixture_actual_result_key_must_keep_candidate_kind() -> None:
    with pytest.raises(ValueError, match="kind must match"):
        GraphFixtureLead(_username_lead("alpha"), actual_key="email:alpha@example.test")

    with pytest.raises(ValueError, match="kind must match"):
        GraphFixtureLead(_username_lead("alpha"), actual_key="username:")


def test_failed_fixture_provider_cannot_also_declare_result_key() -> None:
    with pytest.raises(ValueError, match="cannot also declare"):
        GraphFixtureLead(
            _username_lead("alpha"),
            provider_fails=True,
            actual_key="username:alpha",
        )


def test_fixture_seed_kind_must_match_seed_key() -> None:
    child = _username_lead("alpha")

    with pytest.raises(ValueError, match="seed_key kind must match"):
        evaluate_graph_limit_fixture(
            seed_key="email:seed@example.test",
            seed_kind=LeadKind.USERNAME,
            leads_by_parent={"email:seed@example.test": (GraphFixtureLead(child),)},
            pivot_relevance_by_key={child.key: PivotRelevance.RELEVANT},
            limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
        )


def test_fixture_rejects_orphan_parent_branches() -> None:
    seed = _username_lead("seed")
    child = _username_lead("alpha")
    orphan_child = _username_lead("orphan-child")

    with pytest.raises(ValueError, match="parent keys must be the seed"):
        evaluate_graph_limit_fixture(
            seed_key=seed.key,
            seed_kind=LeadKind.USERNAME,
            leads_by_parent={
                seed.key: (GraphFixtureLead(child),),
                "username:typo-parent": (GraphFixtureLead(orphan_child),),
            },
            pivot_relevance_by_key={
                child.key: PivotRelevance.RELEVANT,
                orphan_child.key: PivotRelevance.WRONG,
            },
            limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
        )
