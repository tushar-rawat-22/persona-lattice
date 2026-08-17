# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from .source_states import SourceRunRecord


def source_run_payload(record: SourceRunRecord) -> dict[str, object]:
    """Serialize one privacy-bounded source state without copying lead values or locators."""

    return {
        "source": record.source_name,
        "lead_kind": record.lead_kind.value,
        "state": record.state.value,
        "reason": record.reason.value,
        "observation_count": record.observation_count,
        "execution_attempted": record.execution_attempted,
        "terminal": record.terminal_for_automation,
    }


def build_source_run_report(records: Iterable[SourceRunRecord]) -> dict[str, object]:
    """Build a stable operator-facing source-state projection for one research scope.

    The projection deliberately has no identifier value, source locator, provider payload,
    credential state or exception text. Canonical observations and lead records remain the
    only owners of those details.
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
    state_counts = Counter(item.state.value for item in ordered)
    reason_counts = Counter(item.reason.value for item in ordered)

    return {
        "record_count": len(ordered),
        "execution_attempted_count": sum(item.execution_attempted for item in ordered),
        "terminal_count": sum(item.terminal_for_automation for item in ordered),
        "state_counts": dict(sorted(state_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "records": [source_run_payload(item) for item in ordered],
    }
