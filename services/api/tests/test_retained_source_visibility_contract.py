# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

from app.cases import _report_payload
from app.intelligence.contracts import LeadKind
from app.intelligence.source_reporting import build_source_run_report
from app.intelligence.source_states import SourceRunReason, SourceRunRecord, SourceRunState
from app.research import QuickResearchReport, ResearchKind


def _records() -> tuple[SourceRunRecord, ...]:
    return (
        SourceRunRecord(
            source_name="github_public_api",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.NOT_FOUND,
            reason=SourceRunReason.NO_MATCH,
        ),
        SourceRunRecord(
            source_name="brave_public_web_index",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.UNAVAILABLE,
            reason=SourceRunReason.OPTIONAL_NOT_CONFIGURED,
        ),
    )


def test_source_run_projection_embeds_deterministic_evaluation_without_sensitive_fields() -> None:
    payload = build_source_run_report(_records())

    assert payload["record_count"] == 2
    assert payload["execution_attempted_count"] == 1
    assert payload["state_counts"] == {"not_found": 1, "unavailable": 1}

    evaluation = payload["evaluation"]
    assert isinstance(evaluation, dict)
    aggregate = evaluation["aggregate"]
    assert aggregate["attempt_count"] == 1
    assert aggregate["completed_attempt_count"] == 1
    assert aggregate["failed_attempt_count"] == 0
    assert aggregate["no_match_count"] == 1
    assert aggregate["optional_not_configured_count"] == 1

    serialized = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "identifier_value",
        "source_locator",
        "provider_payload",
        "exception_text",
        "api_key",
    ):
        assert forbidden not in serialized


def test_quick_case_payload_retains_typed_source_projection() -> None:
    report = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="example-handle",
        observations=(),
        source_runs=_records(),
    )

    payload = _report_payload(report)

    source_runs = payload["source_runs"]
    assert isinstance(source_runs, dict)
    assert source_runs["record_count"] == 2
    assert source_runs["evaluation"]["aggregate"]["attempt_count"] == 1
    assert source_runs["records"][0]["source"] == "brave_public_web_index"
    assert source_runs["records"][1]["source"] == "github_public_api"

    serialized_source_runs = json.dumps(source_runs, sort_keys=True)
    assert "example-handle" not in serialized_source_runs
