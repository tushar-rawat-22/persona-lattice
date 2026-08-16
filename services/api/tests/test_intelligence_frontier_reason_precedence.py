# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
)
from app.intelligence.frontier import FrontierDecision, FrontierLimits, LeadFrontier


def test_duplicate_reason_precedes_depth_limit_for_known_lead() -> None:
    frontier = LeadFrontier(
        seed_key="username:seed",
        seed_kind=LeadKind.USERNAME,
        limits=FrontierLimits(max_depth=0),
    )
    candidate = LeadCandidate(
        kind=LeadKind.USERNAME,
        value="seed",
        comparison_key="seed",
        reason=LeadReason.PUBLIC_USERNAME,
        disposition=LeadDisposition.AUTO_PIVOT,
        source="synthetic_public_source",
        source_locator="https://example.test/profile",
        field_name="username",
    )

    evaluation = frontier.consider(
        candidate,
        parent_key="username:seed",
        parent_depth=0,
    )

    assert evaluation.decision is FrontierDecision.DUPLICATE
