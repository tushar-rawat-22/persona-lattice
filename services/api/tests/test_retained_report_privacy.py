# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

from app.cases import _report_payload
from app.research import QuickObservation, QuickResearchReport, ResearchKind


def test_quick_case_retains_full_provider_evidence_once() -> None:
    unique_payload_marker = "private-marker-that-must-not-be-copied"
    report = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="synthetic-user",
        observations=(
            QuickObservation(
                source="github_public_api",
                source_locator="https://github.com/synthetic-user",
                summary="Synthetic evidence.",
                details={
                    "account_candidate": True,
                    "identity_claim": False,
                    "bio": unique_payload_marker,
                    "email": "public@example.test",
                },
            ),
        ),
    )

    payload = _report_payload(report)
    serialized = json.dumps(payload, sort_keys=True)

    # Arbitrary provider details have one retained owner. The selected public email index
    # deliberately repeats its locator once for direct operator attribution.
    assert serialized.count(unique_payload_marker) == 1
    assert serialized.count("https://github.com/synthetic-user") == 2

    structured = payload["structured_report"]
    assert "source_evidence" not in structured
    assert "public_account_candidates" not in structured
    assert "contradictions" not in structured
    assert structured["public_account_candidate_observation_indexes"] == [0]


def test_structured_report_does_not_copy_seed_value() -> None:
    seed = "unique-seed@example.test"
    report = QuickResearchReport(
        kind=ResearchKind.EMAIL,
        normalized_value=seed,
        observations=(),
    )

    payload = _report_payload(report)
    structured = payload["structured_report"]

    assert "seed" not in structured
    assert json.dumps(structured).count(seed) == 0
