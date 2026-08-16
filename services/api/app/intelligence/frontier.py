# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from .contracts import LeadCandidate, LeadDisposition, LeadKind


class FrontierDecision(StrEnum):
    ENQUEUE = "enqueue"
    ADMITTED = "admitted"
    PROVIDER_FAILED = "provider_failed"
    DUPLICATE = "duplicate"
    REVIEW_REQUIRED = "review_required"
    DISPLAY_ONLY = "display_only"
    BLOCKED = "blocked"
    DEPTH_LIMIT = "depth_limit"
    NODE_LIMIT = "node_limit"
    EDGE_LIMIT = "edge_limit"
    KIND_LIMIT = "kind_limit"
    PARENT_FANOUT_LIMIT = "parent_fanout_limit"


@dataclass(frozen=True, slots=True)
class FrontierLimits:
    """Run-local ceilings for recursive lead expansion.

    The defaults intentionally match or undershoot private V1. Raising them is a
    policy/evaluation decision, not a side effect of adding a provider.
    """

    max_depth: int = 2
    max_nodes: int = 12
    max_edges: int = 24
    max_auto_children_per_parent: int = 6
    max_username_nodes: int = 6
    max_email_nodes: int = 4
    max_phone_nodes: int = 2
    max_url_nodes: int = 6

    def __post_init__(self) -> None:
        numeric = {
            "max_depth": self.max_depth,
            "max_nodes": self.max_nodes,
            "max_edges": self.max_edges,
            "max_auto_children_per_parent": self.max_auto_children_per_parent,
            "max_username_nodes": self.max_username_nodes,
            "max_email_nodes": self.max_email_nodes,
            "max_phone_nodes": self.max_phone_nodes,
            "max_url_nodes": self.max_url_nodes,
        }
        if any(value < 0 for value in numeric.values()):
            raise ValueError("Frontier limits cannot be negative.")
        if self.max_nodes < 1:
            raise ValueError("Frontier max_nodes must include at least the seed node.")

    def kind_limit(self, kind: LeadKind) -> int | None:
        return {
            LeadKind.USERNAME: self.max_username_nodes,
            LeadKind.EMAIL: self.max_email_nodes,
            LeadKind.PHONE: self.max_phone_nodes,
            LeadKind.URL: self.max_url_nodes,
        }.get(kind)


@dataclass(frozen=True, slots=True)
class FrontierEvaluation:
    candidate: LeadCandidate
    decision: FrontierDecision


@dataclass(frozen=True, slots=True)
class _Reservation:
    kind: LeadKind
    parent_key: str


class LeadFrontier:
    """Deterministic run-local admission state for recursive leads.

    `consider()` reserves an automatic candidate before a provider call so the
    same clue cannot cause duplicate network attempts in one run and concurrent
    work cannot oversubscribe graph budgets. `admit()` converts the reservation
    into a real graph node/edge after successful research. `fail()` releases the
    capacity after a failed provider call while keeping the clue in the attempted
    set so one run does not retry it through a different path.
    """

    def __init__(
        self,
        *,
        seed_key: str,
        seed_kind: LeadKind,
        limits: FrontierLimits | None = None,
    ) -> None:
        self.limits = limits or FrontierLimits()
        self._visited = {seed_key}
        self._attempted = {seed_key}
        self._kind_counts: dict[LeadKind, int] = defaultdict(int)
        self._kind_counts[seed_kind] = 1
        self._child_counts: dict[str, int] = defaultdict(int)
        self._edge_count = 0
        self._reservations: dict[str, _Reservation] = {}
        self._reserved_kind_counts: dict[LeadKind, int] = defaultdict(int)
        self._reserved_child_counts: dict[str, int] = defaultdict(int)

    @property
    def node_count(self) -> int:
        return len(self._visited)

    @property
    def edge_count(self) -> int:
        return self._edge_count

    @property
    def reserved_count(self) -> int:
        return len(self._reservations)

    def _release_reservation(self, candidate_key: str) -> _Reservation | None:
        reservation = self._reservations.pop(candidate_key, None)
        if reservation is None:
            return None

        self._reserved_kind_counts[reservation.kind] -= 1
        if self._reserved_kind_counts[reservation.kind] <= 0:
            self._reserved_kind_counts.pop(reservation.kind, None)

        self._reserved_child_counts[reservation.parent_key] -= 1
        if self._reserved_child_counts[reservation.parent_key] <= 0:
            self._reserved_child_counts.pop(reservation.parent_key, None)
        return reservation

    def consider(
        self,
        candidate: LeadCandidate,
        *,
        parent_key: str,
        parent_depth: int,
    ) -> FrontierEvaluation:
        if candidate.disposition is LeadDisposition.REVIEW_REQUIRED:
            return FrontierEvaluation(candidate, FrontierDecision.REVIEW_REQUIRED)
        if candidate.disposition is LeadDisposition.DISPLAY_ONLY:
            return FrontierEvaluation(candidate, FrontierDecision.DISPLAY_ONLY)
        if candidate.disposition is LeadDisposition.BLOCKED:
            return FrontierEvaluation(candidate, FrontierDecision.BLOCKED)
        if candidate.disposition is not LeadDisposition.AUTO_PIVOT:
            raise ValueError(f"Unknown lead disposition: {candidate.disposition!r}")

        # Duplicate knowledge is more specific than a budget stop. Check it first
        # so a known lead discovered at the depth boundary is reported as duplicate
        # instead of making the run look artificially truncated.
        if candidate.key in self._attempted or candidate.key in self._visited:
            return FrontierEvaluation(candidate, FrontierDecision.DUPLICATE)
        if parent_depth >= self.limits.max_depth:
            return FrontierEvaluation(candidate, FrontierDecision.DEPTH_LIMIT)
        if self.node_count + self.reserved_count >= self.limits.max_nodes:
            return FrontierEvaluation(candidate, FrontierDecision.NODE_LIMIT)
        if self.edge_count + self.reserved_count >= self.limits.max_edges:
            return FrontierEvaluation(candidate, FrontierDecision.EDGE_LIMIT)
        if (
            self._child_counts[parent_key] + self._reserved_child_counts[parent_key]
            >= self.limits.max_auto_children_per_parent
        ):
            return FrontierEvaluation(candidate, FrontierDecision.PARENT_FANOUT_LIMIT)

        kind_limit = self.limits.kind_limit(candidate.kind)
        if kind_limit is not None and (
            self._kind_counts[candidate.kind] + self._reserved_kind_counts[candidate.kind]
            >= kind_limit
        ):
            return FrontierEvaluation(candidate, FrontierDecision.KIND_LIMIT)

        self._attempted.add(candidate.key)
        self._reservations[candidate.key] = _Reservation(
            kind=candidate.kind,
            parent_key=parent_key,
        )
        self._reserved_kind_counts[candidate.kind] += 1
        self._reserved_child_counts[parent_key] += 1
        return FrontierEvaluation(candidate, FrontierDecision.ENQUEUE)

    def fail(self, candidate: LeadCandidate) -> FrontierDecision:
        """Release budget reserved for a failed lookup without making it retryable."""

        self._release_reservation(candidate.key)
        return FrontierDecision.PROVIDER_FAILED

    def admit(
        self,
        candidate: LeadCandidate,
        *,
        actual_key: str,
        parent_key: str,
    ) -> FrontierDecision:
        """Admit a successful result node while suppressing normalized duplicates."""

        reservation = self._release_reservation(candidate.key)
        if reservation is None:
            raise ValueError("Lead must be reserved with consider() before admit().")
        if reservation.parent_key != parent_key:
            raise ValueError("Lead reservation parent does not match admit() parent.")

        if actual_key in self._visited:
            return FrontierDecision.DUPLICATE
        if self.node_count >= self.limits.max_nodes:
            return FrontierDecision.NODE_LIMIT
        if self.edge_count >= self.limits.max_edges:
            return FrontierDecision.EDGE_LIMIT

        self._visited.add(actual_key)
        self._kind_counts[candidate.kind] += 1
        self._child_counts[parent_key] += 1
        self._edge_count += 1
        return FrontierDecision.ADMITTED
