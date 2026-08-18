# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

from app.convergence import (
    ConvergedResearchReport,
    PivotReason,
    ResearchNode,
    build_converged_payload,
)
from app.research import QuickObservation, QuickResearchReport, ResearchKind


def test_converged_m5_references_canonical_node_observation() -> None:
    locator = "https://gitlab.com/synthetic-user"
    unique_detail = "detail-owned-only-by-canonical-observation"
    observation = QuickObservation(
        source="gitlab_public_api",
        source_locator=locator,
        summary="Synthetic public account candidate.",
        details={
            "account_candidate": True,
            "identity_claim": False,
            "username": "synthetic-user",
            "bio": unique_detail,
        },
    )
    quick = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="synthetic-user",
        observations=(observation,),
    )
    node = ResearchNode(
        kind=ResearchKind.USERNAME,
        value="synthetic-user",
        depth=0,
        parent_key=None,
        pivot_reason=PivotReason.SEED,
        report=quick,
    )
    report = ConvergedResearchReport(
        seed_kind=ResearchKind.USERNAME,
        seed_value="synthetic-user",
        nodes=(node,),
        edges=(),
        warnings=(),
        truncated=False,
    )

    payload = build_converged_payload(report)
    serialized = json.dumps(payload, sort_keys=True)
    evaluation = payload["m5"]["evaluations"][0]

    assert serialized.count(unique_detail) == 1
    assert serialized.count(locator) == 1
    assert evaluation["candidate_node"] == node.key
    assert evaluation["candidate_observation_index"] == 0
    assert "candidate_source" not in evaluation
    assert "candidate_source_locator" not in evaluation
