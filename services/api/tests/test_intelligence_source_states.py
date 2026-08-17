# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.contracts import LeadKind
from app.intelligence.source_states import (
    SourceRunReason,
    SourceRunRecord,
    SourceRunState,
)


def test_executed_state_requires_observations_and_source_locators() -> None:
    record = SourceRunRecord(
        source_name="github_public_api",
        lead_kind=LeadKind.USERNAME,
        state=SourceRunState.EXECUTED,
        reason=SourceRunReason.RESULTS_RETURNED,
        observation_count=2,
        source_locators=("https://github.com/example", "https://github.com/example/repo"),
    )

    assert record.network_attempted is True
    assert record.terminal_for_automation is True

    with pytest.raises(ValueError, match="at least one observation"):
        SourceRunRecord(
            source_name="github_public_api",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.EXECUTED,
            reason=SourceRunReason.RESULTS_RETURNED,
        )

    with pytest.raises(ValueError, match="source locator"):
        SourceRunRecord(
            source_name="github_public_api",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.EXECUTED,
            reason=SourceRunReason.RESULTS_RETURNED,
            observation_count=1,
        )


def test_not_found_is_an_attempted_zero_observation_terminal_state() -> None:
    record = SourceRunRecord(
        source_name="codeforces_public_api",
        lead_kind=LeadKind.USERNAME,
        state=SourceRunState.NOT_FOUND,
        reason=SourceRunReason.NO_MATCH,
    )

    assert record.observation_count == 0
    assert record.network_attempted is True
    assert record.terminal_for_automation is True


def test_optional_not_configured_is_unavailable_without_claiming_network_execution() -> None:
    record = SourceRunRecord(
        source_name="brave_public_web_index",
        lead_kind=LeadKind.EMAIL,
        state=SourceRunState.UNAVAILABLE,
        reason=SourceRunReason.OPTIONAL_NOT_CONFIGURED,
    )

    assert record.network_attempted is False
    assert record.terminal_for_automation is True


def test_provider_failure_and_remote_rate_limit_record_an_attempt() -> None:
    for reason in (
        SourceRunReason.PROVIDER_FAILURE,
        SourceRunReason.REMOTE_RATE_LIMIT,
    ):
        record = SourceRunRecord(
            source_name="gitlab_public_api",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.UNAVAILABLE,
            reason=reason,
        )
        assert record.network_attempted is True


def test_local_budget_stop_does_not_claim_network_execution() -> None:
    record = SourceRunRecord(
        source_name="github_public_api",
        lead_kind=LeadKind.USERNAME,
        state=SourceRunState.BUDGET_STOPPED,
        reason=SourceRunReason.LOCAL_BUDGET,
    )

    assert record.network_attempted is False
    assert record.terminal_for_automation is True


def test_queue_is_the_only_nonterminal_automatic_state() -> None:
    record = SourceRunRecord(
        source_name="github_public_api",
        lead_kind=LeadKind.USERNAME,
        state=SourceRunState.QUEUED,
        reason=SourceRunReason.ELIGIBLE_QUEUED,
    )

    assert record.network_attempted is False
    assert record.terminal_for_automation is False


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        (SourceRunState.REVIEW_REQUIRED, SourceRunReason.REVIEW_GATE),
        (SourceRunState.DISPLAY_ONLY, SourceRunReason.DISPLAY_ONLY_POLICY),
        (SourceRunState.BLOCKED, SourceRunReason.BLOCKED_POLICY),
    ],
)
def test_nonexecuting_policy_states_are_explicit_and_terminal(
    state: SourceRunState,
    reason: SourceRunReason,
) -> None:
    record = SourceRunRecord(
        source_name="synthetic_policy",
        lead_kind=LeadKind.PHONE,
        state=state,
        reason=reason,
    )

    assert record.network_attempted is False
    assert record.terminal_for_automation is True


def test_state_reason_mismatch_fails_closed() -> None:
    with pytest.raises(ValueError, match="reason is inconsistent"):
        SourceRunRecord(
            source_name="github_public_api",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.NOT_FOUND,
            reason=SourceRunReason.PROVIDER_FAILURE,
        )


def test_nonexecuted_states_cannot_smuggle_observations_or_locators() -> None:
    with pytest.raises(ValueError, match="cannot retain observations"):
        SourceRunRecord(
            source_name="github_public_api",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.NOT_FOUND,
            reason=SourceRunReason.NO_MATCH,
            observation_count=1,
            source_locators=("https://github.com/example",),
        )


def test_source_name_and_locators_are_strictly_bounded_strings() -> None:
    with pytest.raises(ValueError, match="source_name"):
        SourceRunRecord(
            source_name=" github_public_api ",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.NOT_FOUND,
            reason=SourceRunReason.NO_MATCH,
        )

    with pytest.raises(ValueError, match="duplicates"):
        SourceRunRecord(
            source_name="github_public_api",
            lead_kind=LeadKind.USERNAME,
            state=SourceRunState.EXECUTED,
            reason=SourceRunReason.RESULTS_RETURNED,
            observation_count=2,
            source_locators=("https://github.com/example", "https://github.com/example"),
        )
