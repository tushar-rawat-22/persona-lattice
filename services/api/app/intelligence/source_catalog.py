# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .contracts import LeadKind


class SourceStatus(StrEnum):
    ACTIVE = "active"
    OPTIONAL = "optional"
    PLANNED = "planned"
    REVIEW_REQUIRED = "review_required"
    MANUAL_ONLY = "manual_only"
    REFERENCE_ONLY = "reference_only"


class SourceMode(StrEnum):
    LOCAL = "local"
    GOVERNED_PROVIDER = "governed_provider"
    PUBLIC_API = "public_api"
    LICENSED_SEARCH = "licensed_search"
    OPEN_STANDARD = "open_standard"
    USER_AUTHORIZED = "user_authorized"
    MANUAL = "manual"


class SourceCostClass(StrEnum):
    LOCAL = "local"
    ZERO_DIRECT_COST = "zero_direct_cost"
    FREE_TIER = "free_tier"
    METERED = "metered"
    MANUAL = "manual"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SourceCapability:
    """Static capability declaration for one logical research source.

    This catalog does not execute anything. It lets the planner answer what a
    source *could* accept/emit before an adapter, credential or network call is
    considered. Execution policy remains authoritative in the provider/research
    layer.
    """

    name: str
    accepts: frozenset[LeadKind]
    emits: frozenset[LeadKind]
    status: SourceStatus
    mode: SourceMode
    cost_class: SourceCostClass
    terms_reviewed: bool
    recursive_eligible: bool
    zero_budget_eligible: bool
    auth_required: bool = False
    priority: int = 100
    note: str = ""

    def __post_init__(self) -> None:
        if not self.name or self.name.strip() != self.name:
            raise ValueError("Source capability name must be non-empty and trimmed.")
        if not self.accepts:
            raise ValueError(f"Source {self.name!r} must declare at least one accepted lead kind.")
        if self.priority < 0:
            raise ValueError("Source capability priority cannot be negative.")
        if self.recursive_eligible and self.status not in {
            SourceStatus.ACTIVE,
            SourceStatus.OPTIONAL,
        }:
            raise ValueError("Only active or optional sources may be recursive-eligible.")
        if self.recursive_eligible and not self.terms_reviewed:
            raise ValueError("Recursive-eligible sources require a reviewed source policy.")
        if self.zero_budget_eligible and self.cost_class in {
            SourceCostClass.METERED,
            SourceCostClass.UNKNOWN,
        }:
            raise ValueError("Metered/unknown-cost sources cannot be zero-budget eligible.")


# The catalog describes current logical sources plus reviewed integration targets.
# Planned entries are architecture declarations only: they cannot execute until a
# real adapter, source-policy review, fixtures and execution gate exist.
SOURCE_CATALOG: tuple[SourceCapability, ...] = (
    SourceCapability(
        name="local_normalization",
        accepts=frozenset({LeadKind.EMAIL, LeadKind.URL}),
        emits=frozenset({LeadKind.DOMAIN}),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.LOCAL,
        cost_class=SourceCostClass.LOCAL,
        terms_reviewed=True,
        recursive_eligible=True,
        zero_budget_eligible=True,
        priority=5,
        note="Deterministic local parsing only; no external identity claim.",
    ),
    SourceCapability(
        name="libphonenumber_metadata",
        accepts=frozenset({LeadKind.PHONE}),
        emits=frozenset({LeadKind.LOCATION}),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.LOCAL,
        cost_class=SourceCostClass.LOCAL,
        terms_reviewed=True,
        recursive_eligible=True,
        zero_budget_eligible=True,
        priority=10,
        note="Numbering-plan/carrier/region metadata; not subscriber identity.",
    ),
    SourceCapability(
        name="sherlock",
        accepts=frozenset({LeadKind.USERNAME}),
        emits=frozenset({LeadKind.URL}),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.GOVERNED_PROVIDER,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        terms_reviewed=True,
        recursive_eligible=True,
        zero_budget_eligible=True,
        priority=20,
        note="Pinned reviewed site allowlist; account hits remain candidates only.",
    ),
    SourceCapability(
        name="github_public_api",
        accepts=frozenset({LeadKind.USERNAME}),
        emits=frozenset(
            {
                LeadKind.USERNAME,
                LeadKind.EMAIL,
                LeadKind.URL,
                LeadKind.NAME,
                LeadKind.ORGANIZATION,
                LeadKind.LOCATION,
            }
        ),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        terms_reviewed=True,
        recursive_eligible=True,
        zero_budget_eligible=True,
        priority=25,
        note="Public profile fields only; same-handle remains insufficient identity evidence.",
    ),
    SourceCapability(
        name="gitlab_public_api",
        accepts=frozenset({LeadKind.USERNAME, LeadKind.EMAIL}),
        emits=frozenset(
            {
                LeadKind.USERNAME,
                LeadKind.EMAIL,
                LeadKind.URL,
                LeadKind.NAME,
                LeadKind.ORGANIZATION,
                LeadKind.LOCATION,
            }
        ),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        terms_reviewed=True,
        recursive_eligible=True,
        zero_budget_eligible=True,
        priority=30,
        note="Username and exact public-email lookup paths only.",
    ),
    SourceCapability(
        name="codeforces_public_api",
        accepts=frozenset({LeadKind.USERNAME}),
        emits=frozenset({LeadKind.USERNAME, LeadKind.EMAIL, LeadKind.ORGANIZATION}),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        terms_reviewed=True,
        recursive_eligible=True,
        zero_budget_eligible=True,
        priority=35,
        note="Public profile fields only.",
    ),
    SourceCapability(
        name="public_dns_infrastructure",
        accepts=frozenset({LeadKind.URL, LeadKind.DOMAIN}),
        emits=frozenset(),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.OPEN_STANDARD,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        terms_reviewed=True,
        recursive_eligible=True,
        zero_budget_eligible=True,
        priority=40,
        note="Public hostname infrastructure only; never a subject/device IP lead.",
    ),
    SourceCapability(
        name="brave_public_web_index",
        accepts=frozenset(
            {LeadKind.USERNAME, LeadKind.EMAIL, LeadKind.PHONE, LeadKind.URL}
        ),
        emits=frozenset(),
        status=SourceStatus.OPTIONAL,
        mode=SourceMode.LICENSED_SEARCH,
        cost_class=SourceCostClass.METERED,
        terms_reviewed=True,
        recursive_eligible=True,
        zero_budget_eligible=False,
        auth_required=True,
        priority=60,
        note="Exact-identifier public-web search; snippets do not become new leads.",
    ),
    SourceCapability(
        name="bluesky_public_profile",
        accepts=frozenset({LeadKind.USERNAME}),
        emits=frozenset(
            {LeadKind.USERNAME, LeadKind.URL, LeadKind.NAME, LeadKind.LOCATION}
        ),
        status=SourceStatus.PLANNED,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        terms_reviewed=False,
        recursive_eligible=False,
        zero_budget_eligible=True,
        priority=70,
        note="Adapter target: public profile lookup by reviewed handle semantics.",
    ),
    SourceCapability(
        name="gravatar_public_profile",
        accepts=frozenset({LeadKind.EMAIL}),
        emits=frozenset(
            {LeadKind.URL, LeadKind.NAME, LeadKind.ORGANIZATION, LeadKind.LOCATION}
        ),
        status=SourceStatus.PLANNED,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.FREE_TIER,
        terms_reviewed=False,
        recursive_eligible=False,
        zero_budget_eligible=True,
        auth_required=False,
        priority=75,
        note="Adapter target: SHA-256 email identifier to openly accessible profile data.",
    ),
    SourceCapability(
        name="webfinger_activitypub",
        accepts=frozenset({LeadKind.URL}),
        emits=frozenset({LeadKind.URL, LeadKind.USERNAME, LeadKind.NAME}),
        status=SourceStatus.PLANNED,
        mode=SourceMode.OPEN_STANDARD,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        terms_reviewed=False,
        recursive_eligible=False,
        zero_budget_eligible=True,
        priority=80,
        note="Adapter target for recognized federated profile URLs; generic usernames are insufficient.",
    ),
    SourceCapability(
        name="rdap_domain_registry",
        accepts=frozenset({LeadKind.DOMAIN}),
        emits=frozenset({LeadKind.ORGANIZATION}),
        status=SourceStatus.PLANNED,
        mode=SourceMode.OPEN_STANDARD,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        terms_reviewed=False,
        recursive_eligible=False,
        zero_budget_eligible=True,
        priority=85,
        note="Adapter target for registry/domain metadata; registry redaction remains authoritative.",
    ),
    SourceCapability(
        name="google_people_authorized",
        accepts=frozenset({LeadKind.EMAIL, LeadKind.PHONE, LeadKind.NAME}),
        emits=frozenset(
            {LeadKind.EMAIL, LeadKind.PHONE, LeadKind.NAME, LeadKind.ORGANIZATION}
        ),
        status=SourceStatus.PLANNED,
        mode=SourceMode.USER_AUTHORIZED,
        cost_class=SourceCostClass.FREE_TIER,
        terms_reviewed=False,
        recursive_eligible=False,
        zero_budget_eligible=True,
        auth_required=True,
        priority=90,
        note="Future explicit user-authorized import; not public people search.",
    ),
)


SOURCE_BY_NAME = {source.name: source for source in SOURCE_CATALOG}
if len(SOURCE_BY_NAME) != len(SOURCE_CATALOG):
    raise RuntimeError("Source capability catalog contains duplicate names.")


def sources_for_lead(
    kind: LeadKind,
    *,
    include_optional: bool = True,
    include_planned: bool = False,
    zero_budget_only: bool = False,
    recursive_only: bool = False,
) -> tuple[SourceCapability, ...]:
    """Return deterministic source capabilities that declare support for a lead kind."""

    allowed_statuses = {SourceStatus.ACTIVE}
    if include_optional:
        allowed_statuses.add(SourceStatus.OPTIONAL)
    if include_planned:
        allowed_statuses.add(SourceStatus.PLANNED)

    selected = [
        source
        for source in SOURCE_CATALOG
        if kind in source.accepts
        and source.status in allowed_statuses
        and (not zero_budget_only or source.zero_budget_eligible)
        and (not recursive_only or source.recursive_eligible)
    ]
    return tuple(sorted(selected, key=lambda source: (source.priority, source.name)))
