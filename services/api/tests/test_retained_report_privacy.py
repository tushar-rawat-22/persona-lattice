# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

from app.cases import _report_payload
from app.research import QuickObservation, QuickResearchReport, ResearchKind


_WEB_QUICK_RESEARCH = Path(__file__).parents[3] / "apps" / "web" / "app" / "admin" / "quick-research.tsx"


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

    # Provider details, selected connected values and provider provenance each have one retained
    # owner: the canonical observation. The structured report stores references only.
    assert serialized.count(unique_payload_marker) == 1
    assert serialized.count("public@example.test") == 1
    assert serialized.count("https://github.com/synthetic-user") == 1

    structured = payload["structured_report"]
    connected = structured["connected_identifiers"]
    assert connected == [
        {
            "kind": "email",
            "observation_index": 0,
            "detail_field": "email",
            "status": "observed_public_field",
        }
    ]
    assert "value" not in connected[0]
    assert "source" not in connected[0]
    assert "source_locator" not in connected[0]
    assert "source_evidence" not in structured
    assert "public_account_candidates" not in structured
    assert "contradictions" not in structured
    assert structured["public_account_candidate_observation_indexes"] == [0]


def test_private_ui_resolves_quick_references_without_api_hydration() -> None:
    source = _WEB_QUICK_RESEARCH.read_text(encoding="utf-8")

    assert "resolveConnectedIdentifier" in source
    assert "CONNECTED_IDENTIFIER_FIELD_BY_KIND" in source
    assert "item.observation_index" in source
    assert "item.detail_field" in source
    assert "Stored connected-field reference could not be resolved safely." in source


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
