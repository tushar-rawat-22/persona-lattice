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


def source_provider_policy_record(
    *,
    source_name: str,
    lead_kind: LeadKind,
) -> SourceRunRecord:
    """Record a provider-policy rejection that happened before execution."""

    return SourceRunRecord(
        source_name=source_name,
        lead_kind=lead_kind,
        state=SourceRunState.BLOCKED,
        reason=SourceRunReason.PROVIDER_POLICY,
    )


def source_credential_not_configured_record(
    *,
    source_name: str,
    lead_kind: LeadKind,
) -> SourceRunRecord:
    """Record a required server-side credential missing before provider contact."""

    return SourceRunRecord(
        source_name=source_name,
        lead_kind=lead_kind,
        state=SourceRunState.UNAVAILABLE,
        reason=SourceRunReason.CREDENTIAL_NOT_CONFIGURED,
    )


def source_malformed_result_record(
    *,
    source_name: str,
    lead_kind: LeadKind,
) -> SourceRunRecord:
    """Record a provider attempt whose returned result failed runtime validation.

    Use this only when the runtime has already received provider output and can
    prove that the failure is post-attempt. Generic validation failures remain
    deliberately unclassified until their execution phase is known.
    """

    return SourceRunRecord(
        source_name=source_name,
        lead_kind=lead_kind,
        state=SourceRunState.UNAVAILABLE,
        reason=SourceRunReason.MALFORMED_RESULT,
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
