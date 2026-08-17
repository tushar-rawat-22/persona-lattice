# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import LeadKind
from app.intelligence.source_evaluation import build_source_evaluation_counters
from app.intelligence.source_states import SourceRunReason, SourceRunRecord, SourceRunState


def _matrix() -> tuple[SourceRunRecord, ...]:
    return (
        SourceRunRecord("fixture_profile", LeadKind.USERNAME, SourceRunState.EXECUTED, SourceRunReason.RESULTS_RETURNED, 3),
        SourceRunRecord("fixture_profile", LeadKind.USERNAME, SourceRunState.NOT_FOUND, SourceRunReason.NO_MATCH),
        SourceRunRecord("fixture_scheduler", LeadKind.EMAIL, SourceRunState.QUEUED, SourceRunReason.ELIGIBLE_QUEUED),
        SourceRunRecord("fixture_scheduler", LeadKind.PHONE, SourceRunState.REVIEW_REQUIRED, SourceRunReason.REVIEW_GATE),
        SourceRunRecord("fixture_scheduler", LeadKind.NAME, SourceRunState.DISPLAY_ONLY, SourceRunReason.DISPLAY_ONLY_POLICY),
        SourceRunRecord("fixture_scheduler", LeadKind.LOCATION, SourceRunState.BLOCKED, SourceRunReason.BLOCKED_POLICY),
        SourceRunRecord("fixture_optional", LeadKind.URL, SourceRunState.UNAVAILABLE, SourceRunReason.OPTIONAL_NOT_CONFIGURED),
        SourceRunRecord("fixture_remote", LeadKind.USERNAME, SourceRunState.UNAVAILABLE, SourceRunReason.EXECUTION_FAILURE),
        SourceRunRecord("fixture_remote", LeadKind.USERNAME, SourceRunState.UNAVAILABLE, SourceRunReason.REMOTE_RATE_LIMIT),
        SourceRunRecord("fixture_budget", LeadKind.DOMAIN, SourceRunState.BUDGET_STOPPED, SourceRunReason.LOCAL_BUDGET),
    )


def test_fixture_matrix_covers_the_entire_current_state_and_reason_vocabulary() -> None:
    records = _matrix()
    assert {item.state for item in records} == set(SourceRunState)
    assert {item.reason for item in records} == set(SourceRunReason)


def test_fixture_matrix_locks_attempt_failure_and_no_match_semantics() -> None:
    aggregate = build_source_evaluation_counters(_matrix())["aggregate"]
    assert aggregate == {
        "record_count": 10,
        "attempt_count": 4,
        "completed_attempt_count": 2,
        "failed_attempt_count": 2,
        "unclassified_attempt_count": 0,
        "result_record_count": 1,
        "no_match_count": 1,
        "observation_count": 3,
        "remote_rate_limit_count": 1,
        "execution_failure_count": 1,
        "local_budget_stop_count": 1,
        "optional_not_configured_count": 1,
        "queued_count": 1,
        "review_required_count": 1,
        "display_only_count": 1,
        "blocked_count": 1,
    }
    assert aggregate["attempt_count"] == (
        aggregate["completed_attempt_count"]
        + aggregate["failed_attempt_count"]
        + aggregate["unclassified_attempt_count"]
    )


def test_fixture_matrix_is_order_invariant() -> None:
    records = _matrix()
    expected = build_source_evaluation_counters(records)
    assert build_source_evaluation_counters(reversed(records)) == expected
    assert build_source_evaluation_counters(records[3:] + records[:3]) == expected


def test_fixture_matrix_keeps_local_optional_and_remote_outcomes_separate() -> None:
    by_source = build_source_evaluation_counters(_matrix())["by_source"]
    assert by_source["fixture_optional"]["attempt_count"] == 0
    assert by_source["fixture_optional"]["optional_not_configured_count"] == 1
    assert by_source["fixture_budget"]["attempt_count"] == 0
    assert by_source["fixture_budget"]["local_budget_stop_count"] == 1
    assert by_source["fixture_remote"]["attempt_count"] == 2
    assert by_source["fixture_remote"]["failed_attempt_count"] == 2
    assert by_source["fixture_remote"]["execution_failure_count"] == 1
    assert by_source["fixture_remote"]["remote_rate_limit_count"] == 1
    assert by_source["fixture_profile"]["completed_attempt_count"] == 2
    assert by_source["fixture_profile"]["failed_attempt_count"] == 0
    assert by_source["fixture_profile"]["no_match_count"] == 1
    assert by_source["fixture_profile"]["observation_count"] == 3
