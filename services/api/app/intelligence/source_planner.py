# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass

from .contracts import LeadKind
from .source_catalog import SOURCE_CATALOG, SourceCapability, SourceStatus


@dataclass(frozen=True, slots=True)
class SourcePlan:
    """Non-executing capability plan for one lead kind.

    The plan is safe to expose to orchestration/UI because membership does not
    authorize a provider call. `active`/`optional` still require the live
    execution policy; `planned` explicitly has no execution authority.
    """

    kind: LeadKind
    active: tuple[SourceCapability, ...]
    optional: tuple[SourceCapability, ...]
    planned: tuple[SourceCapability, ...]
    excluded_by_budget: tuple[SourceCapability, ...]

    @property
    def has_current_coverage(self) -> bool:
        return bool(self.active or self.optional)

    @property
    def has_zero_spend_current_coverage(self) -> bool:
        return any(source.zero_spend_eligible for source in (*self.active, *self.optional))


def _ordered(sources: list[SourceCapability]) -> tuple[SourceCapability, ...]:
    return tuple(sorted(sources, key=lambda source: (source.priority, source.name)))


def build_source_plan(
    kind: LeadKind,
    *,
    zero_spend_only: bool = False,
) -> SourcePlan:
    """Describe current and planned source coverage without executing anything."""

    active: list[SourceCapability] = []
    optional: list[SourceCapability] = []
    planned: list[SourceCapability] = []
    excluded_by_budget: list[SourceCapability] = []

    for source in SOURCE_CATALOG:
        if kind not in source.accepts:
            continue

        if source.status is SourceStatus.PLANNED:
            planned.append(source)
            continue
        if source.status not in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}:
            continue
        if not source.recursive_eligible or not source.source_policy_reviewed:
            continue
        if zero_spend_only and not source.zero_spend_eligible:
            excluded_by_budget.append(source)
            continue

        if source.status is SourceStatus.ACTIVE:
            active.append(source)
        else:
            optional.append(source)

    return SourcePlan(
        kind=kind,
        active=_ordered(active),
        optional=_ordered(optional),
        planned=_ordered(planned),
        excluded_by_budget=_ordered(excluded_by_budget),
    )
