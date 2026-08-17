# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .contracts import LeadKind


class SourceRunState(StrEnum):
    """Operator-visible state for one source against one research lead."""

    EXECUTED = "executed"
    NOT_FOUND = "not_found"
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
    ELIGIBLE_QUEUED = "eligible_queued"
    REVIEW_GATE = "review_gate"
    DISPLAY_ONLY_POLICY = "display_only_policy"
    BLOCKED_POLICY = "blocked_policy"
    OPTIONAL_NOT_CONFIGURED = "optional_not_configured"
    PROVIDER_FAILURE = "provider_failure"
    REMOTE_RATE_LIMIT = "remote_rate_limit"
    LOCAL_BUDGET = "local_budget"


_ALLOWED_REASONS: dict[SourceRunState, frozenset[SourceRunReason]] = {
    SourceRunState.EXECUTED: frozenset({SourceRunReason.RESULTS_RETURNED}),
    SourceRunState.NOT_FOUND: frozenset({SourceRunReason.NO_MATCH}),
    SourceRunState.QUEUED: frozenset({SourceRunReason.ELIGIBLE_QUEUED}),
    SourceRunState.REVIEW_REQUIRED: frozenset({SourceRunReason.REVIEW_GATE}),
    SourceRunState.DISPLAY_ONLY: frozenset({SourceRunReason.DISPLAY_ONLY_POLICY}),
    SourceRunState.BLOCKED: frozenset({SourceRunReason.BLOCKED_POLICY}),
    SourceRunState.UNAVAILABLE: frozenset(
        {
            SourceRunReason.OPTIONAL_NOT_CONFIGURED,
            SourceRunReason.PROVIDER_FAILURE,
            SourceRunReason.REMOTE_RATE_LIMIT,
        }
    ),
    SourceRunState.BUDGET_STOPPED: frozenset({SourceRunReason.LOCAL_BUDGET}),
}


@dataclass(frozen=True, slots=True)
class SourceRunRecord:
    """Privacy-bounded report record for source scheduling/execution state.

    This contract deliberately stores the lead kind and source outcome, not the
    lead value. Existing lead/evidence records remain the authority for the
    identifier itself and its provenance.
    """

    source_name: str
    lead_kind: LeadKind
    state: SourceRunState
    reason: SourceRunReason
    observation_count: int = 0
    source_locators: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_name or self.source_name.strip() != self.source_name:
            raise ValueError("Source run source_name must be non-empty and trimmed.")
        if self.reason not in _ALLOWED_REASONS[self.state]:
            raise ValueError("Source run reason is inconsistent with its state.")
        if self.observation_count < 0:
            raise ValueError("Source run observation_count cannot be negative.")
        if any(not value or value.strip() != value for value in self.source_locators):
            raise ValueError("Source run locators must be non-empty and trimmed.")
        if len(set(self.source_locators)) != len(self.source_locators):
            raise ValueError("Source run locators cannot contain duplicates.")

        if self.state is SourceRunState.EXECUTED:
            if self.observation_count < 1:
                raise ValueError("Executed source runs require at least one observation.")
            if not self.source_locators:
                raise ValueError("Executed source runs require at least one source locator.")
        elif self.observation_count != 0 or self.source_locators:
            raise ValueError(
                "Non-executed-result source states cannot retain observations or source locators."
            )

    @property
    def execution_attempted(self) -> bool:
        """Whether the state proves that source execution reached an attempt."""

        if self.state in {SourceRunState.EXECUTED, SourceRunState.NOT_FOUND}:
            return True
        return self.reason in {
            SourceRunReason.PROVIDER_FAILURE,
            SourceRunReason.REMOTE_RATE_LIMIT,
        }

    @property
    def terminal_for_automation(self) -> bool:
        """Whether automatic execution has no remaining action for this record."""

        return self.state is not SourceRunState.QUEUED
