# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

from app.cases import _report_payload, hydrate_case_report_connected_identifiers
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
    assert "source_evidence" not in structured
    assert "public_account_candidates" not in structured
    assert "contradictions" not in structured
    assert structured["public_account_candidate_observation_indexes"] == [0]

    hydrated = hydrate_case_report_connected_identifiers(payload)
    hydrated_item = hydrated["structured_report"]["connected_identifiers"][0]
    assert hydrated_item["value"] == "public@example.test"
    assert hydrated_item["source"] == "github_public_api"
    assert hydrated_item["source_locator"] == "https://github.com/synthetic-user"

    # Response hydration is transient and does not mutate the retained payload.
    assert "value" not in payload["structured_report"]["connected_identifiers"][0]


def test_connected_identifier_hydration_fails_closed_on_bad_reference() -> None:
    payload = {
        "observations": [
            {
                "source": "github_public_api",
                "source_locator": "https://github.com/synthetic-user",
                "details": {"email": "public@example.test"},
            }
        ],
        "structured_report": {
            "connected_identifiers": [
                {
                    "kind": "email",
                    "observation_index": 9,
                    "detail_field": "email",
                    "status": "observed_public_field",
                }
            ]
        },
    }

    try:
        hydrate_case_report_connected_identifiers(payload)
    except ValueError as exc:
        assert "out of range" in str(exc)
    else:
        raise AssertionError("Malformed connected-field references must fail closed.")


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
