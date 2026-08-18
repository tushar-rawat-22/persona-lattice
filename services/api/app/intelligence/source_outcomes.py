# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from ..providers.errors import (
    ProviderAccountUnavailableError,
    ProviderAuthError,
    ProviderExecutionError,
    ProviderPolicyError,
    ProviderPublicWebOptOutError,
    ProviderRateBudgetExceeded,
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTimeoutError,
    ProviderTransientError,
    ProviderValidationError,
)
from .contracts import LeadKind
from .source_states import SourceRunReason, SourceRunRecord, SourceRunState


def source_result_record(*, source_name: str, lead_kind: LeadKind, observation_count: int) -> SourceRunRecord:
    if observation_count < 0:
        raise ValueError("observation_count cannot be negative.")
    if observation_count == 0:
        return SourceRunRecord(source_name, lead_kind, SourceRunState.NOT_FOUND, SourceRunReason.NO_MATCH)
    return SourceRunRecord(
        source_name, lead_kind, SourceRunState.EXECUTED, SourceRunReason.RESULTS_RETURNED, observation_count
    )


def source_execution_failure_record(*, source_name: str, lead_kind: LeadKind, remote_rate_limited: bool = False) -> SourceRunRecord:
    return SourceRunRecord(
        source_name=source_name,
        lead_kind=lead_kind,
        state=SourceRunState.UNAVAILABLE,
        reason=SourceRunReason.REMOTE_RATE_LIMIT if remote_rate_limited else SourceRunReason.EXECUTION_FAILURE,
    )


def source_withheld_record(*, source_name: str, lead_kind: LeadKind, reason: SourceRunReason) -> SourceRunRecord:
    if reason not in {SourceRunReason.PUBLIC_WEB_OPT_OUT, SourceRunReason.ACCOUNT_UNAVAILABLE}:
        raise ValueError("withheld source runs require a neutral withheld reason")
    return SourceRunRecord(source_name, lead_kind, SourceRunState.WITHHELD, reason)


def source_provider_policy_record(*, source_name: str, lead_kind: LeadKind) -> SourceRunRecord:
    return SourceRunRecord(source_name, lead_kind, SourceRunState.BLOCKED, SourceRunReason.PROVIDER_POLICY)


def source_credential_not_configured_record(*, source_name: str, lead_kind: LeadKind) -> SourceRunRecord:
    return SourceRunRecord(source_name, lead_kind, SourceRunState.UNAVAILABLE, SourceRunReason.CREDENTIAL_NOT_CONFIGURED)


def source_malformed_result_record(*, source_name: str, lead_kind: LeadKind) -> SourceRunRecord:
    return SourceRunRecord(source_name, lead_kind, SourceRunState.UNAVAILABLE, SourceRunReason.MALFORMED_RESULT)


def source_optional_not_configured_record(*, source_name: str, lead_kind: LeadKind) -> SourceRunRecord:
    return SourceRunRecord(source_name, lead_kind, SourceRunState.UNAVAILABLE, SourceRunReason.OPTIONAL_NOT_CONFIGURED)


def source_local_budget_record(*, source_name: str, lead_kind: LeadKind) -> SourceRunRecord:
    return SourceRunRecord(source_name, lead_kind, SourceRunState.BUDGET_STOPPED, SourceRunReason.LOCAL_BUDGET)


def source_provider_exception_record(*, source_name: str, lead_kind: LeadKind, exc: BaseException) -> SourceRunRecord | None:
    """Map a provider exception only when its execution phase is provable."""

    if isinstance(exc, ProviderRateBudgetExceeded):
        return source_local_budget_record(source_name=source_name, lead_kind=lead_kind)
    if isinstance(exc, ProviderPolicyError):
        return source_provider_policy_record(source_name=source_name, lead_kind=lead_kind)
    if isinstance(exc, ProviderAuthError):
        return source_credential_not_configured_record(source_name=source_name, lead_kind=lead_kind)
    if isinstance(exc, ProviderPublicWebOptOutError):
        return source_withheld_record(
            source_name=source_name,
            lead_kind=lead_kind,
            reason=SourceRunReason.PUBLIC_WEB_OPT_OUT,
        )
    if isinstance(exc, ProviderAccountUnavailableError):
        return source_withheld_record(
            source_name=source_name,
            lead_kind=lead_kind,
            reason=SourceRunReason.ACCOUNT_UNAVAILABLE,
        )
    if isinstance(exc, ProviderResultValidationError):
        return source_malformed_result_record(source_name=source_name, lead_kind=lead_kind)
    if isinstance(exc, ProviderRemoteRateLimitError):
        return source_execution_failure_record(
            source_name=source_name, lead_kind=lead_kind, remote_rate_limited=True
        )
    if isinstance(exc, (ProviderTimeoutError, ProviderTransientError, ProviderResponseTooLarge)):
        return source_execution_failure_record(source_name=source_name, lead_kind=lead_kind)
    if type(exc) is ProviderExecutionError:
        return source_execution_failure_record(source_name=source_name, lead_kind=lead_kind)
    if isinstance(exc, ProviderValidationError):
        return None
    return None
