# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import LeadKind
from app.intelligence.source_reporting import build_source_run_report, source_run_payload
from app.intelligence.source_states import SourceRunReason, SourceRunRecord, SourceRunState


def _record(
    source: str,
    kind: LeadKind,
    state: SourceRunState,
    reason: SourceRunReason,
    *,
    observations: int = 0,
) -> SourceRunRecord:
    return SourceRunRecord(
        source_name=source,
        lead_kind=kind,
        state=state,
        reason=reason,
        observation_count=observations,
    )


def test_source_run_payload_exposes_state_not_personal_data() -> None:
    payload = source_run_payload(
        _record(
            "github_public_api",
            LeadKind.USERNAME,
            SourceRunState.EXECUTED,
            SourceRunReason.RESULTS_RETURNED,
            observations=2,
        )
    )

    assert payload == {
        "source": "github_public_api",
        "lead_kind": "username",
        "state": "executed",
        "reason": "results_returned",
        "observation_count": 2,
        "execution_attempted": True,
        "terminal": True,
    }
    assert "value" not in payload
    assert "source_locator" not in payload
    assert "payload" not in payload
    assert "credential" not in payload
    assert "exception" not in payload


def test_source_run_report_is_deterministic_and_counts_attempts() -> None:
    records = (
        _record(
            "gitlab_public_api",
            LeadKind.USERNAME,
            SourceRunState.UNAVAILABLE,
            SourceRunReason.EXECUTION_FAILURE,
        ),
        _record(
            "brave_public_web_index",
            LeadKind.USERNAME,
            SourceRunState.UNAVAILABLE,
            SourceRunReason.OPTIONAL_NOT_CONFIGURED,
        ),
        _record(
            "github_public_api",
            LeadKind.USERNAME,
            SourceRunState.NOT_FOUND,
            SourceRunReason.NO_MATCH,
        ),
    )

    forward = build_source_run_report(records)
    reverse = build_source_run_report(reversed(records))

    assert forward == reverse
    assert forward["record_count"] == 3
    assert forward["execution_attempted_count"] == 2
    assert forward["terminal_count"] == 3
    assert forward["state_counts"] == {"not_found": 1, "unavailable": 2}
    assert forward["reason_counts"] == {
        "execution_failure": 1,
        "no_match": 1,
        "optional_not_configured": 1,
    }
    assert [item["source"] for item in forward["records"]] == [
        "brave_public_web_index",
        "github_public_api",
        "gitlab_public_api",
    ]


def test_remote_rate_limit_and_local_budget_remain_distinct() -> None:
    report = build_source_run_report(
        (
            _record(
                "codeforces_public_api",
                LeadKind.USERNAME,
                SourceRunState.UNAVAILABLE,
                SourceRunReason.REMOTE_RATE_LIMIT,
            ),
            _record(
                "github_public_api",
                LeadKind.USERNAME,
                SourceRunState.BUDGET_STOPPED,
                SourceRunReason.LOCAL_BUDGET,
            ),
        )
    )

    assert report["execution_attempted_count"] == 1
    assert report["state_counts"] == {"budget_stopped": 1, "unavailable": 1}
    assert report["reason_counts"] == {"local_budget": 1, "remote_rate_limit": 1}


def test_empty_scope_is_explicit_not_missing() -> None:
    assert build_source_run_report(()) == {
        "record_count": 0,
        "execution_attempted_count": 0,
        "terminal_count": 0,
        "state_counts": {},
        "reason_counts": {},
        "records": [],
        "evaluation": {
            "aggregate": {
                "record_count": 0,
                "attempt_count": 0,
                "completed_attempt_count": 0,
                "failed_attempt_count": 0,
                "unclassified_attempt_count": 0,
                "result_record_count": 0,
                "no_match_count": 0,
                "withheld_count": 0,
                "observation_count": 0,
                "public_web_opt_out_count": 0,
                "account_unavailable_count": 0,
                "remote_rate_limit_count": 0,
                "execution_failure_count": 0,
                "malformed_result_count": 0,
                "local_budget_stop_count": 0,
                "optional_not_configured_count": 0,
                "missing_secret_config_count": 0,
                "provider_policy_block_count": 0,
                "queued_count": 0,
                "review_required_count": 0,
                "display_only_count": 0,
                "blocked_count": 0,
            },
            "by_source": {},
        },
    }
