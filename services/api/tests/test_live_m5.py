# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.convergence import ConvergedResearchReport, PivotReason, ResearchNode
from app.live_m5 import evaluate_live_m5
from app.research import QuickObservation, QuickResearchReport, ResearchKind


def _node(
    kind: ResearchKind,
    value: str,
    *,
    depth: int,
    reason: PivotReason,
    observations: tuple[QuickObservation, ...] = (),
) -> ResearchNode:
    return ResearchNode(
        kind=kind,
        value=value,
        depth=depth,
        parent_key=None if depth == 0 else "seed",
        pivot_reason=reason,
        report=QuickResearchReport(
            kind=kind,
            normalized_value=value,
            observations=observations,
        ),
    )


def test_live_m5_same_username_candidate_remains_uncalibrated_weak_triage() -> None:
    candidate = QuickObservation(
        source="gitlab_public_api",
        source_locator="https://gitlab.com/public-user",
        summary="Public account candidate.",
        details={"account_candidate": True, "identity_claim": False, "username": "public-user"},
    )
    report = ConvergedResearchReport(
        seed_kind=ResearchKind.USERNAME,
        seed_value="public-user",
        nodes=(
            _node(
                ResearchKind.USERNAME,
                "public-user",
                depth=0,
                reason=PivotReason.SEED,
                observations=(candidate,),
            ),
        ),
        edges=(),
        warnings=(),
        truncated=False,
    )

    result = evaluate_live_m5(report)
    evaluation = result["evaluations"][0]

    assert evaluation["evidence_score"] == 10
    assert evaluation["outcome"] == "insufficient_evidence"
    assert evaluation["calibration_status"] == "uncalibrated"
    assert evaluation["is_identity_claim"] is False


def test_live_m5_exact_original_email_overlap_is_possible_not_identity_claim() -> None:
    candidate = QuickObservation(
        source="gitlab_public_api",
        source_locator="https://gitlab.com/public-user",
        summary="Public account candidate.",
        details={
            "account_candidate": True,
            "identity_claim": False,
            "username": "public-user",
            "public_email": "known@example.test",
        },
    )
    report = ConvergedResearchReport(
        seed_kind=ResearchKind.EMAIL,
        seed_value="known@example.test",
        nodes=(
            _node(
                ResearchKind.EMAIL,
                "known@example.test",
                depth=0,
                reason=PivotReason.SEED,
            ),
            _node(
                ResearchKind.USERNAME,
                "public-user",
                depth=1,
                reason=PivotReason.PUBLIC_USERNAME,
                observations=(candidate,),
            ),
        ),
        edges=(),
        warnings=(),
        truncated=False,
    )

    result = evaluate_live_m5(report)
    evaluation = result["evaluations"][0]

    assert evaluation["evidence_score"] == 55
    assert evaluation["outcome"] == "possible_match"
    assert evaluation["is_identity_claim"] is False
    factors = {factor["kind"]: factor for factor in evaluation["factors"]}
    assert factors["exact_confirmed_identifier_overlap"]["applied_weight"] == 55
    assert factors["same_username"]["applied_weight"] == 0


def test_live_m5_does_not_bootstrap_strong_overlap_from_discovered_email() -> None:
    candidate = QuickObservation(
        source="github_public_api",
        source_locator="https://github.com/seeduser",
        summary="Public account candidate.",
        details={
            "account_candidate": True,
            "identity_claim": False,
            "login": "seeduser",
            "email": "discovered@example.test",
        },
    )
    report = ConvergedResearchReport(
        seed_kind=ResearchKind.USERNAME,
        seed_value="seeduser",
        nodes=(
            _node(
                ResearchKind.USERNAME,
                "seeduser",
                depth=0,
                reason=PivotReason.SEED,
                observations=(candidate,),
            ),
            _node(
                ResearchKind.EMAIL,
                "discovered@example.test",
                depth=1,
                reason=PivotReason.PUBLIC_EMAIL,
            ),
        ),
        edges=(),
        warnings=(),
        truncated=False,
    )

    result = evaluate_live_m5(report)
    evaluation = result["evaluations"][0]

    assert evaluation["evidence_score"] == 10
    assert [factor["kind"] for factor in evaluation["factors"]] == ["same_username"]
