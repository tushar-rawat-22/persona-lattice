# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import LeadKind
from app.intelligence.source_evaluation import build_source_evaluation_counters
from app.intelligence.source_states import SourceRunReason, SourceRunRecord, SourceRunState


def _record(
    source: str,
    state: SourceRunState,
    reason: SourceRunReason,
    *,
    observations: int = 0,
) -> SourceRunRecord:
    return SourceRunRecord(
        source_name=source,
        lead_kind=LeadKind.USERNAME,
        state=state,
        reason=reason,
        observation_count=observations,
    )


def test_evaluation_counters_separate_provider_failure_from_local_stops() -> None:
    records = (
        _record(
            "github_public_api",
            SourceRunState.EXECUTED,
            SourceRunReason.RESULTS_RETURNED,
            observations=2,
        ),
        _record(
            "github_public_api",
            SourceRunState.NOT_FOUND,
            SourceRunReason.NO_MATCH,
        ),
        _record(
            "gitlab_public_api",
            SourceRunState.UNAVAILABLE,
            SourceRunReason.EXECUTION_FAILURE,
        ),
        _record(
            "codeforces_public_api",
            SourceRunState.UNAVAILABLE,
            SourceRunReason.REMOTE_RATE_LIMIT,
        ),
        _record(
            "github_public_api",
            SourceRunState.BUDGET_STOPPED,
            SourceRunReason.LOCAL_BUDGET,
        ),
        _record(
            "brave_public_web_index",
            SourceRunState.UNAVAILABLE,
            SourceRunReason.OPTIONAL_NOT_CONFIGURED,
        ),
    )

    counters = build_source_evaluation_counters(records)
    aggregate = counters["aggregate"]

    assert aggregate == {
        "record_count": 6,
        "attempt_count": 4,
        "completed_attempt_count": 2,
        "failed_attempt_count": 2,
        "unclassified_attempt_count": 0,
        "result_record_count": 1,
        "no_match_count": 1,
        "observation_count": 2,
        "remote_rate_limit_count": 1,
        "execution_failure_count": 1,
        "local_budget_stop_count": 1,
        "optional_not_configured_count": 1,
        "queued_count": 0,
        "review_required_count": 0,
        "display_only_count": 0,
        "blocked_count": 0,
    }
    assert aggregate["attempt_count"] == (
        aggregate["completed_attempt_count"]
        + aggregate["failed_attempt_count"]
        + aggregate["unclassified_attempt_count"]
    )


def test_evaluation_is_deterministic_and_keeps_per_source_counters() -> None:
    records = (
        _record(
            "gitlab_public_api",
            SourceRunState.NOT_FOUND,
            SourceRunReason.NO_MATCH,
        ),
        _record(
            "github_public_api",
            SourceRunState.EXECUTED,
            SourceRunReason.RESULTS_RETURNED,
            observations=1,
        ),
        _record(
            "github_public_api",
            SourceRunState.UNAVAILABLE,
            SourceRunReason.REMOTE_RATE_LIMIT,
        ),
    )

    forward = build_source_evaluation_counters(records)
    reverse = build_source_evaluation_counters(reversed(records))

    assert forward == reverse
    assert list(forward["by_source"]) == ["github_public_api", "gitlab_public_api"]
    assert forward["by_source"]["github_public_api"]["attempt_count"] == 2
    assert forward["by_source"]["github_public_api"]["result_record_count"] == 1
    assert forward["by_source"]["github_public_api"]["remote_rate_limit_count"] == 1
    assert forward["by_source"]["gitlab_public_api"]["no_match_count"] == 1


def test_evaluation_counts_scheduler_states_without_calling_them_attempts() -> None:
    records = (
        _record("sherlock", SourceRunState.QUEUED, SourceRunReason.ELIGIBLE_QUEUED),
        _record("sherlock", SourceRunState.REVIEW_REQUIRED, SourceRunReason.REVIEW_GATE),
        _record("sherlock", SourceRunState.DISPLAY_ONLY, SourceRunReason.DISPLAY_ONLY_POLICY),
        _record("sherlock", SourceRunState.BLOCKED, SourceRunReason.BLOCKED_POLICY),
    )

    aggregate = build_source_evaluation_counters(records)["aggregate"]

    assert aggregate["attempt_count"] == 0
    assert aggregate["queued_count"] == 1
    assert aggregate["review_required_count"] == 1
    assert aggregate["display_only_count"] == 1
    assert aggregate["blocked_count"] == 1


def test_evaluation_output_contains_no_personal_or_provider_payload_fields() -> None:
    counters = build_source_evaluation_counters(
        (
            _record(
                "github_public_api",
                SourceRunState.EXECUTED,
                SourceRunReason.RESULTS_RETURNED,
                observations=1,
            ),
        )
    )
    serialized = repr(counters)

    for forbidden in (
        "identifier_value",
        "source_locator",
        "credential",
        "exception",
        "payload",
    ):
        assert forbidden not in serialized


def test_empty_evaluation_scope_is_explicit() -> None:
    counters = build_source_evaluation_counters(())

    assert counters["by_source"] == {}
    assert counters["aggregate"]["record_count"] == 0
    assert counters["aggregate"]["attempt_count"] == 0
    assert counters["aggregate"]["observation_count"] == 0
