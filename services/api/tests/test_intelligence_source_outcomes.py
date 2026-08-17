# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.contracts import LeadKind
from app.intelligence.source_outcomes import (
    source_credential_not_configured_record,
    source_execution_failure_record,
    source_local_budget_record,
    source_malformed_result_record,
    source_optional_not_configured_record,
    source_provider_policy_record,
    source_result_record,
)
from app.intelligence.source_states import SourceRunReason, SourceRunState


def test_result_with_observations_is_executed() -> None:
    record = source_result_record(
        source_name="github_public_api",
        lead_kind=LeadKind.USERNAME,
        observation_count=2,
    )

    assert record.state is SourceRunState.EXECUTED
    assert record.reason is SourceRunReason.RESULTS_RETURNED
    assert record.observation_count == 2
    assert record.execution_attempted is True


def test_empty_result_is_not_found_not_unavailable() -> None:
    record = source_result_record(
        source_name="github_public_api",
        lead_kind=LeadKind.USERNAME,
        observation_count=0,
    )

    assert record.state is SourceRunState.NOT_FOUND
    assert record.reason is SourceRunReason.NO_MATCH
    assert record.execution_attempted is True


def test_result_rejects_negative_observation_count() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        source_result_record(
            source_name="github_public_api",
            lead_kind=LeadKind.USERNAME,
            observation_count=-1,
        )


def test_remote_rate_limit_is_attempted_unavailability() -> None:
    record = source_execution_failure_record(
        source_name="codeforces_public_api",
        lead_kind=LeadKind.USERNAME,
        remote_rate_limited=True,
    )

    assert record.state is SourceRunState.UNAVAILABLE
    assert record.reason is SourceRunReason.REMOTE_RATE_LIMIT
    assert record.execution_attempted is True


def test_execution_failure_is_attempted_unavailability() -> None:
    record = source_execution_failure_record(
        source_name="public_dns_infrastructure",
        lead_kind=LeadKind.URL,
    )

    assert record.state is SourceRunState.UNAVAILABLE
    assert record.reason is SourceRunReason.EXECUTION_FAILURE
    assert record.execution_attempted is True


def test_provider_policy_block_is_explicit_without_claiming_execution() -> None:
    record = source_provider_policy_record(
        source_name="github_public_api",
        lead_kind=LeadKind.USERNAME,
    )

    assert record.state is SourceRunState.BLOCKED
    assert record.reason is SourceRunReason.PROVIDER_POLICY
    assert record.execution_attempted is False


def test_missing_required_credential_is_explicit_without_claiming_execution() -> None:
    record = source_credential_not_configured_record(
        source_name="synthetic_credentialed_provider",
        lead_kind=LeadKind.EMAIL,
    )

    assert record.state is SourceRunState.UNAVAILABLE
    assert record.reason is SourceRunReason.CREDENTIAL_NOT_CONFIGURED
    assert record.execution_attempted is False


def test_malformed_result_is_an_attempted_failure() -> None:
    record = source_malformed_result_record(
        source_name="github_public_api",
        lead_kind=LeadKind.USERNAME,
    )

    assert record.state is SourceRunState.UNAVAILABLE
    assert record.reason is SourceRunReason.MALFORMED_RESULT
    assert record.execution_attempted is True


def test_optional_not_configured_never_claims_execution_attempt() -> None:
    record = source_optional_not_configured_record(
        source_name="brave_public_web_index",
        lead_kind=LeadKind.EMAIL,
    )

    assert record.state is SourceRunState.UNAVAILABLE
    assert record.reason is SourceRunReason.OPTIONAL_NOT_CONFIGURED
    assert record.execution_attempted is False


def test_local_budget_stop_never_claims_provider_contact() -> None:
    record = source_local_budget_record(
        source_name="github_public_api",
        lead_kind=LeadKind.USERNAME,
    )

    assert record.state is SourceRunState.BUDGET_STOPPED
    assert record.reason is SourceRunReason.LOCAL_BUDGET
    assert record.execution_attempted is False
