# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.convergence import PivotReason, ResearchNode, _node_payload
from app.intelligence.contracts import LeadKind
from app.intelligence.source_outcomes import (
    source_execution_failure_record,
    source_local_budget_record,
    source_result_record,
)
from app.research import QuickResearchReport, ResearchKind


@dataclass(frozen=True, slots=True)
class _LegacyReportWithoutSourceRuns:
    normalized_value: str
    observations: tuple = ()
    warnings: tuple[str, ...] = ()


def _node(report: QuickResearchReport) -> ResearchNode:
    return ResearchNode(
        kind=ResearchKind.USERNAME,
        value="alice",
        depth=0,
        parent_key=None,
        pivot_reason=PivotReason.SEED,
        report=report,
    )


def test_node_payload_projects_typed_source_runs_without_identifiers() -> None:
    report = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="alice",
        observations=(),
        source_runs=(
            source_result_record(
                source_name="github_public_api",
                lead_kind=LeadKind.USERNAME,
                observation_count=1,
            ),
            source_execution_failure_record(
                source_name="codeforces_public_api",
                lead_kind=LeadKind.USERNAME,
                remote_rate_limited=True,
            ),
            source_local_budget_record(
                source_name="sherlock",
                lead_kind=LeadKind.USERNAME,
            ),
        ),
    )

    payload = _node_payload(_node(report))
    source_runs = payload["source_runs"]

    assert source_runs["record_count"] == 3
    assert source_runs["execution_attempted_count"] == 2
    assert source_runs["state_counts"] == {
        "budget_stopped": 1,
        "executed": 1,
        "unavailable": 1,
    }
    assert source_runs["reason_counts"] == {
        "local_budget": 1,
        "remote_rate_limit": 1,
        "results_returned": 1,
    }
    assert "alice" not in repr(source_runs)
    assert "source_locator" not in repr(source_runs)
    assert "details" not in repr(source_runs)


def test_quick_report_without_source_runs_gets_explicit_empty_projection() -> None:
    report = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="alice",
        observations=(),
    )

    payload = _node_payload(_node(report))

    assert payload["source_runs"] == {
        "record_count": 0,
        "execution_attempted_count": 0,
        "terminal_count": 0,
        "state_counts": {},
        "reason_counts": {},
        "records": [],
    }


def test_node_payload_rejects_report_without_typed_source_run_contract() -> None:
    legacy_report = _LegacyReportWithoutSourceRuns(normalized_value="alice")
    node = ResearchNode(
        kind=ResearchKind.USERNAME,
        value="alice",
        depth=0,
        parent_key=None,
        pivot_reason=PivotReason.SEED,
        report=legacy_report,  # type: ignore[arg-type]
    )

    with pytest.raises(AttributeError, match="source_runs"):
        _node_payload(node)
