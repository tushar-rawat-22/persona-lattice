# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .contracts import LeadKind
from .source_states import SourceRunReason, SourceRunRecord, SourceRunState


def source_result_record(
    *,
    source_name: str,
    lead_kind: LeadKind,
    observation_count: int,
) -> SourceRunRecord:
    """Record a completed source call from its actual result cardinality."""

    if observation_count < 0:
        raise ValueError("observation_count cannot be negative.")
    if observation_count == 0:
        return SourceRunRecord(
            source_name=source_name,
            lead_kind=lead_kind,
            state=SourceRunState.NOT_FOUND,
            reason=SourceRunReason.NO_MATCH,
        )
    return SourceRunRecord(
        source_name=source_name,
        lead_kind=lead_kind,
        state=SourceRunState.EXECUTED,
        reason=SourceRunReason.RESULTS_RETURNED,
        observation_count=observation_count,
    )


def source_execution_failure_record(
    *,
    source_name: str,
    lead_kind: LeadKind,
    remote_rate_limited: bool = False,
) -> SourceRunRecord:
    """Record a provider attempt that failed after execution was entered.

    Callers must not use this for policy, credential or configuration failures
    that happened before an execution attempt. Those states need an explicit
    non-attempt outcome rather than being mislabeled as provider contact.
    """

    return SourceRunRecord(
        source_name=source_name,
        lead_kind=lead_kind,
        state=SourceRunState.UNAVAILABLE,
        reason=(
            SourceRunReason.REMOTE_RATE_LIMIT
            if remote_rate_limited
            else SourceRunReason.EXECUTION_FAILURE
        ),
    )


def source_optional_not_configured_record(
    *,
    source_name: str,
    lead_kind: LeadKind,
) -> SourceRunRecord:
    """Record an optional source that was intentionally not attempted."""

    return SourceRunRecord(
        source_name=source_name,
        lead_kind=lead_kind,
        state=SourceRunState.UNAVAILABLE,
        reason=SourceRunReason.OPTIONAL_NOT_CONFIGURED,
    )


def source_local_budget_record(
    *,
    source_name: str,
    lead_kind: LeadKind,
) -> SourceRunRecord:
    """Record a local pre-call budget stop without implying provider contact."""

    return SourceRunRecord(
        source_name=source_name,
        lead_kind=lead_kind,
        state=SourceRunState.BUDGET_STOPPED,
        reason=SourceRunReason.LOCAL_BUDGET,
    )
