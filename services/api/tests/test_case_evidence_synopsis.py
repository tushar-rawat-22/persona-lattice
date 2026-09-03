# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.case_synopsis import build_case_evidence_synopsis


def test_quick_synopsis_keeps_only_bounded_decision_metadata() -> None:
    report = {
        "observations": [{"source_locator": "https://secret.example.test/person"}],
        "warnings": ["coverage limited"],
        "source_runs": {"state_counts": {"completed": 2, "failed": 1}},
        "structured_report": {
            "executive_summary": {
                "observation_count": 3,
                "source_count": 2,
                "sources": ["source_a", "source_b"],
            },
            "contradiction_observation_indexes": [1],
            "coverage_gaps": ["gap one", "gap two"],
        },
    }

    synopsis = build_case_evidence_synopsis(report)

    assert synopsis.mode == "quick"
    assert synopsis.available is True
    assert synopsis.observation_count == 3
    assert synopsis.source_count == 2
    assert synopsis.sources == ("source_a", "source_b")
    assert synopsis.warning_count == 1
    assert synopsis.contradiction_count == 1
    assert synopsis.source_state_counts == {"completed": 2, "failed": 1}
    assert synopsis.coverage_gap_count == 2
    assert synopsis.truncated is False
    assert synopsis.m5_present is False
    assert "secret.example.test" not in repr(synopsis)


def test_converged_synopsis_aggregates_nodes_without_copying_provenance() -> None:
    report = {
        "converged_report": {
            "executive_summary": {
                "source_count": 2,
                "sources": ["source_a", "source_b"],
                "truncated": True,
            },
            "nodes": [
                {
                    "source_runs": {"state_counts": {"completed": 1, "failed": 1}},
                    "observations": [
                        {
                            "source_locator": "https://private.example.test/a",
                            "details": {"contradiction": True},
                        },
                        {"details": {}},
                    ],
                },
                {
                    "source_runs": {"state_counts": {"completed": 2}},
                    "observations": [{"details": {"account_state": "illegal"}}],
                },
            ],
            "lead_graph": {"blocked_field_names": ["private_email"]},
            "warnings": ["bounded traversal"],
            "m5": {"score": "must-not-be-projected"},
        }
    }

    synopsis = build_case_evidence_synopsis(report)

    assert synopsis.mode == "converged"
    assert synopsis.available is True
    assert synopsis.observation_count == 3
    assert synopsis.source_count == 2
    assert synopsis.sources == ("source_a", "source_b")
    assert synopsis.warning_count == 1
    assert synopsis.contradiction_count == 2
    assert synopsis.source_state_counts == {"completed": 3, "failed": 1}
    assert synopsis.coverage_gap_count == 1
    assert synopsis.truncated is True
    assert synopsis.m5_present is True
    assert "private.example.test" not in repr(synopsis)
    assert "must-not-be-projected" not in repr(synopsis)


def test_unknown_or_legacy_shape_is_explicitly_unavailable() -> None:
    synopsis = build_case_evidence_synopsis({"legacy": {"observations": []}})

    assert synopsis.mode == "legacy_or_unknown"
    assert synopsis.available is False
    assert synopsis.observation_count is None
    assert synopsis.source_count is None
    assert synopsis.sources == ()
    assert synopsis.source_state_counts == {}
    assert synopsis.truncated is None
