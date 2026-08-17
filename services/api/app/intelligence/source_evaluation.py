# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

from .source_states import SourceRunReason, SourceRunRecord, SourceRunState


def _counter_payload(records: tuple[SourceRunRecord, ...]) -> dict[str, int]:
    """Summarize source outcomes without deriving probabilistic quality claims."""

    state_counts = Counter(item.state for item in records)
    reason_counts = Counter(item.reason for item in records)
    attempted = tuple(item for item in records if item.execution_attempted)
    completed = tuple(
        item
        for item in attempted
        if item.state in {SourceRunState.EXECUTED, SourceRunState.NOT_FOUND}
    )
    failed = tuple(item for item in attempted if item.state is SourceRunState.UNAVAILABLE)
    unclassified_attempted = len(attempted) - len(completed) - len(failed)

    return {
        "record_count": len(records),
        "attempt_count": len(attempted),
        "completed_attempt_count": len(completed),
        "failed_attempt_count": len(failed),
        "unclassified_attempt_count": unclassified_attempted,
        "result_record_count": state_counts[SourceRunState.EXECUTED],
        "no_match_count": state_counts[SourceRunState.NOT_FOUND],
        "observation_count": sum(item.observation_count for item in records),
        "remote_rate_limit_count": reason_counts[SourceRunReason.REMOTE_RATE_LIMIT],
        "execution_failure_count": reason_counts[SourceRunReason.EXECUTION_FAILURE],
        "local_budget_stop_count": reason_counts[SourceRunReason.LOCAL_BUDGET],
        "optional_not_configured_count": reason_counts[SourceRunReason.OPTIONAL_NOT_CONFIGURED],
        "queued_count": state_counts[SourceRunState.QUEUED],
        "review_required_count": state_counts[SourceRunState.REVIEW_REQUIRED],
        "display_only_count": state_counts[SourceRunState.DISPLAY_ONLY],
        "blocked_count": state_counts[SourceRunState.BLOCKED],
    }


def build_source_evaluation_counters(
    records: Iterable[SourceRunRecord],
) -> dict[str, object]:
    """Build deterministic aggregate/per-source counters for M10-style evaluation.

    These are descriptive counters, not reliability probabilities or identity-quality
    scores. The output deliberately excludes identifier values, source locators,
    provider payloads, credentials, exception text and wall-clock timing.
    """

    ordered = tuple(
        sorted(
            records,
            key=lambda item: (
                item.source_name,
                item.lead_kind.value,
                item.state.value,
                item.reason.value,
                item.observation_count,
            ),
        )
    )
    grouped: dict[str, list[SourceRunRecord]] = defaultdict(list)
    for item in ordered:
        grouped[item.source_name].append(item)

    return {
        "aggregate": _counter_payload(ordered),
        "by_source": {
            source_name: _counter_payload(tuple(grouped[source_name]))
            for source_name in sorted(grouped)
        },
    }
