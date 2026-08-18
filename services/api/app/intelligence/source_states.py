# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .contracts import LeadKind


class SourceRunState(StrEnum):
    """Operator-visible state for one source against one research lead."""

    EXECUTED = "executed"
    NOT_FOUND = "not_found"
    WITHHELD = "withheld"
    QUEUED = "queued"
    REVIEW_REQUIRED = "review_required"
    DISPLAY_ONLY = "display_only"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    BUDGET_STOPPED = "budget_stopped"


class SourceRunReason(StrEnum):
    """Stable reason vocabulary behind source-state reporting."""

    RESULTS_RETURNED = "results_returned"
    NO_MATCH = "no_match"
    PUBLIC_WEB_OPT_OUT = "public_web_opt_out"
    ACCOUNT_UNAVAILABLE = "account_unavailable"
    ELIGIBLE_QUEUED = "eligible_queued"
    REVIEW_GATE = "review_gate"
    DISPLAY_ONLY_POLICY = "display_only_policy"
    BLOCKED_POLICY = "blocked_policy"
    PROVIDER_POLICY = "provider_policy"
    OPTIONAL_NOT_CONFIGURED = "optional_not_configured"
    CREDENTIAL_NOT_CONFIGURED = "credential_not_configured"
    EXECUTION_FAILURE = "execution_failure"
    REMOTE_RATE_LIMIT = "remote_rate_limit"
    MALFORMED_RESULT = "malformed_result"
    LOCAL_BUDGET = "local_budget"


_ALLOWED_REASONS: dict[SourceRunState, frozenset[SourceRunReason]] = {
    SourceRunState.EXECUTED: frozenset({SourceRunReason.RESULTS_RETURNED}),
    SourceRunState.NOT_FOUND: frozenset({SourceRunReason.NO_MATCH}),
    SourceRunState.WITHHELD: frozenset(
        {
            SourceRunReason.PUBLIC_WEB_OPT_OUT,
            SourceRunReason.ACCOUNT_UNAVAILABLE,
        }
    ),
    SourceRunState.QUEUED: frozenset({SourceRunReason.ELIGIBLE_QUEUED}),
    SourceRunState.REVIEW_REQUIRED: frozenset({SourceRunReason.REVIEW_GATE}),
    SourceRunState.DISPLAY_ONLY: frozenset({SourceRunReason.DISPLAY_ONLY_POLICY}),
    SourceRunState.BLOCKED: frozenset(
        {
            SourceRunReason.BLOCKED_POLICY,
            SourceRunReason.PROVIDER_POLICY,
        }
    ),
    SourceRunState.UNAVAILABLE: frozenset(
        {
            SourceRunReason.OPTIONAL_NOT_CONFIGURED,
            SourceRunReason.CREDENTIAL_NOT_CONFIGURED,
            SourceRunReason.EXECUTION_FAILURE,
            SourceRunReason.REMOTE_RATE_LIMIT,
            SourceRunReason.MALFORMED_RESULT,
        }
    ),
    SourceRunState.BUDGET_STOPPED: frozenset({SourceRunReason.LOCAL_BUDGET}),
}


@dataclass(frozen=True, slots=True)
class SourceRunRecord:
    """Privacy-bounded report record for source scheduling/execution state.

    This contract stores state metadata only. Lead values and exact source
    locators remain in their existing lead/Observation records so the report does
    not create another copy of personal identifiers or provenance URLs.
    """

    source_name: str
    lead_kind: LeadKind
    state: SourceRunState
    reason: SourceRunReason
    observation_count: int = 0

    def __post_init__(self) -> None:
        if not self.source_name or self.source_name.strip() != self.source_name:
            raise ValueError("Source run source_name must be non-empty and trimmed.")
        if self.reason not in _ALLOWED_REASONS[self.state]:
            raise ValueError("Source run reason is inconsistent with its state.")
        if self.observation_count < 0:
            raise ValueError("Source run observation_count cannot be negative.")

        if self.state is SourceRunState.EXECUTED:
            if self.observation_count < 1:
                raise ValueError("Executed source runs require at least one observation.")
        elif self.observation_count != 0:
            raise ValueError("Non-result source states cannot retain an observation count.")

    @property
    def execution_attempted(self) -> bool:
        """Whether the state proves that source execution reached an attempt."""

        if self.state in {
            SourceRunState.EXECUTED,
            SourceRunState.NOT_FOUND,
            SourceRunState.WITHHELD,
        }:
            return True
        return self.reason in {
            SourceRunReason.EXECUTION_FAILURE,
            SourceRunReason.REMOTE_RATE_LIMIT,
            SourceRunReason.MALFORMED_RESULT,
        }

    @property
    def terminal_for_automation(self) -> bool:
        """Whether automatic execution has no remaining action for this record."""

        return self.state is not SourceRunState.QUEUED
