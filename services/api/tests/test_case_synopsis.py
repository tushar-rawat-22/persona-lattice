# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from uuid import UUID

from app.case_synopsis import build_case_synopsis
from app.cases import StoredCase
from app.research import ResearchKind


_NOW = datetime(2026, 9, 4, 0, 0, tzinfo=UTC)
_CASE_ID = UUID("11111111-1111-4111-8111-111111111111")


def _record(report: dict[str, object], *, kind: ResearchKind = ResearchKind.USERNAME) -> StoredCase:
    return StoredCase(
        id=_CASE_ID,
        created_at=_NOW,
        expires_at=_NOW + timedelta(days=30),
        seed_kind=kind,
        seed_value="sensitive-seed-value",
        report=report,
    )


def test_quick_synopsis_summarizes_evidence_without_copying_provider_details() -> None:
    report = {
        "kind": "username",
        "normalized_value": "sensitive-seed-value",
        "observations": [
            {
                "source": "github_public_api",
                "source_locator": "https://example.test/private-locator",
                "summary": "Public profile candidate.",
                "details": {"email": "do-not-copy@example.test", "account_candidate": True},
            },
            {
                "source": "sherlock",
                "source_locator": "https://example.test/second-locator",
                "summary": "Provider contradiction.",
                "details": {"contradiction": True, "secret_field": "do-not-copy-secret"},
            },
        ],
        "warnings": ["One source was unavailable."],
        "source_runs": {
            "record_count": 2,
            "state_counts": {"success": 1, "execution_failure": 1},
            "reason_counts": {"result": 1, "provider_error": 1},
            "evaluation": {"result_count": 1, "failure_count": 1},
            "records": [{"source": "not-copied"}],
        },
        "structured_report": {
            "executive_summary": {
                "connected_identifier_count": 1,
                "public_account_candidate_count": 1,
            },
            "contradiction_observation_indexes": [1],
            "coverage_gaps": ["Same-handle evidence needs corroboration."],
        },
    }

    synopsis = build_case_synopsis(_record(report))

    assert synopsis["synopsis_version"] == "analyst-case-synopsis-v1"
    assert synopsis["case"] == {
        "id": str(_CASE_ID),
        "created_at": _NOW.isoformat(),
        "expires_at": (_NOW + timedelta(days=30)).isoformat(),
        "seed_kind": "username",
    }
    assert synopsis["evidence_summary"] == {
        "observation_count": 2,
        "source_count": 2,
        "sources": ["github_public_api", "sherlock"],
        "connected_identifier_count": 1,
        "public_account_candidate_count": 1,
        "contradiction_count": 1,
        "warning_count": 1,
        "coverage_gap_count": 1,
        "identity_probability": None,
        "identity_claim": False,
    }
    assert synopsis["contradiction_observation_indexes"] == [1]
    serialized = json.dumps(synopsis, sort_keys=True)
    assert "sensitive-seed-value" not in serialized
    assert "private-locator" not in serialized
    assert "do-not-copy@example.test" not in serialized
    assert "do-not-copy-secret" not in serialized
    assert '"records"' not in serialized


def test_quick_synopsis_recovers_contradiction_flag_when_index_is_missing() -> None:
    report = {
        "observations": [
            {
                "source": "sherlock",
                "details": {"account_state": "illegal"},
            }
        ],
        "structured_report": {"contradiction_observation_indexes": []},
    }

    synopsis = build_case_synopsis(_record(report))

    assert synopsis["contradiction_observation_indexes"] == [0]
    assert synopsis["evidence_summary"]["contradiction_count"] == 1


def test_converged_synopsis_aggregates_nodes_without_copying_graph_values_or_m5_scores() -> None:
    report = {
        "kind": "username",
        "normalized_value": "sensitive-seed-value",
        "converged_report": {
            "executive_summary": {
                "research_node_count": 2,
                "pivot_edge_count": 1,
                "lead_decision_count": 3,
                "truncated": True,
            },
            "nodes": [
                {
                    "key": "username:sensitive-seed-value",
                    "source_runs": {
                        "record_count": 1,
                        "state_counts": {"success": 1},
                        "reason_counts": {"result": 1},
                    },
                    "observations": [
                        {
                            "source": "github_public_api",
                            "source_locator": "https://example.test/locator-a",
                            "details": {"private_detail": "never-copy-a"},
                        }
                    ],
                },
                {
                    "key": "email:private@example.test",
                    "source_runs": {
                        "record_count": 2,
                        "state_counts": {"success": 1, "not_configured": 1},
                        "reason_counts": {"result": 1, "optional_not_configured": 1},
                    },
                    "observations": [
                        {
                            "source": "brave_public_web_index",
                            "source_locator": "https://example.test/locator-b",
                            "details": {"contradiction": True, "private_detail": "never-copy-b"},
                        }
                    ],
                },
            ],
            "lead_graph": {
                "decision_counts": {"admitted": 1, "duplicate": 2},
                "decisions": [{"normalized_value": "private@example.test"}],
            },
            "warnings": ["Graph stopped at its configured bound."],
            "m5": {"score": 0.91, "do_not_copy": "m5-private-payload"},
        },
    }

    synopsis = build_case_synopsis(_record(report))

    assert synopsis["workflow"] == {
        "mode": "converged",
        "truncated": True,
        "research_node_count": 2,
        "pivot_edge_count": 1,
        "lead_decision_count": 3,
        "lead_decision_counts": {"admitted": 1, "duplicate": 2},
    }
    assert synopsis["source_states"] == {
        "record_count": 3,
        "state_counts": {"not_configured": 1, "success": 2},
        "reason_counts": {"optional_not_configured": 1, "result": 2},
    }
    assert synopsis["contradiction_references"] == [
        {"node_index": 1, "observation_index": 0}
    ]
    serialized = json.dumps(synopsis, sort_keys=True)
    for forbidden in (
        "sensitive-seed-value",
        "private@example.test",
        "locator-a",
        "locator-b",
        "never-copy-a",
        "never-copy-b",
        "m5-private-payload",
        "0.91",
    ):
        assert forbidden not in serialized
    assert any("non-probabilistic" in item for item in synopsis["method_limits"])


def test_synopsis_is_deterministic_for_partial_legacy_payload() -> None:
    synopsis = build_case_synopsis(_record({"kind": "username"}))

    assert synopsis["workflow"] == {"mode": "quick", "truncated": False}
    assert synopsis["evidence_summary"]["observation_count"] == 0
    assert synopsis["evidence_summary"]["identity_probability"] is None
    assert synopsis["evidence_summary"]["identity_claim"] is False
    assert synopsis["source_states"]["state_counts"] == {}
