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
    REFERENCE = "reference"


class SourceCostClass(StrEnum):
    LOCAL = "local"
    ZERO_DIRECT_COST = "zero_direct_cost"
    FREE_TIER = "free_tier"
    METERED = "metered"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class SourceCredentialClass(StrEnum):
    NONE = "none"
    FREE_API_KEY = "free_api_key"
    METERED_API_KEY = "metered_api_key"
    API_KEY_UNKNOWN_COST = "api_key_unknown_cost"
    USER_OAUTH = "user_oauth"
    MANUAL = "manual"


_ZERO_SPEND_COST_CLASSES = frozenset(
    {
        SourceCostClass.LOCAL,
        SourceCostClass.ZERO_DIRECT_COST,
        SourceCostClass.FREE_TIER,
    }
)
_ZERO_SPEND_CREDENTIAL_CLASSES = frozenset(
    {
        SourceCredentialClass.NONE,
        SourceCredentialClass.FREE_API_KEY,
    }
)


@dataclass(frozen=True, slots=True)
class SourceCapability:
    """Static capability declaration for one logical research source.

    This catalog never executes a source. It lets the planner answer what a
    source *could* accept/emit before an adapter, credential or network call is
    considered. The existing provider/research execution policy remains the
    authority that decides whether a call is actually allowed.
    """

    name: str
    accepts: frozenset[LeadKind]
    emits: frozenset[LeadKind]
    status: SourceStatus
    mode: SourceMode
    cost_class: SourceCostClass
    credential_class: SourceCredentialClass
    source_policy_reviewed: bool
    recursive_eligible: bool
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
        if self.recursive_eligible and not self.source_policy_reviewed:
            raise ValueError("Recursive-eligible sources require a reviewed source policy.")
        if self.mode is SourceMode.USER_AUTHORIZED and (
            self.credential_class is not SourceCredentialClass.USER_OAUTH
        ):
            raise ValueError("User-authorized sources must declare user OAuth credentials.")
        if self.mode is SourceMode.MANUAL and (
            self.credential_class is not SourceCredentialClass.MANUAL
        ):
            raise ValueError("Manual sources must declare manual credentials/workflow.")
        if self.cost_class is SourceCostClass.METERED and (
            self.credential_class is not SourceCredentialClass.METERED_API_KEY
        ):
            raise ValueError("Metered sources must declare a metered API credential.")

    @property
    def zero_spend_eligible(self) -> bool:
        """Whether current source policy requires no paid credential/service tier."""

        return (
            self.cost_class in _ZERO_SPEND_COST_CLASSES
            and self.credential_class in _ZERO_SPEND_CREDENTIAL_CLASSES
        )


SOURCE_CATALOG: tuple[SourceCapability, ...] = (
    SourceCapability(
        name="local_normalization",
        accepts=frozenset({LeadKind.EMAIL, LeadKind.URL}),
        emits=frozenset({LeadKind.DOMAIN}),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.LOCAL,
        cost_class=SourceCostClass.LOCAL,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
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
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
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
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
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
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
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
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
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
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=35,
        note="Public profile fields only.",
    ),
    SourceCapability(
        name="bluesky_public_profile",
        accepts=frozenset({LeadKind.USERNAME}),
        emits=frozenset({LeadKind.USERNAME, LeadKind.NAME}),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=37,
        note=(
            "Unauthenticated public AppView profile lookup for syntactically valid AT handles only; "
            "public-web opt-out and unavailable-account states are neutral completed outcomes."
        ),
    ),
    SourceCapability(
        name="public_dns_infrastructure",
        accepts=frozenset({LeadKind.URL, LeadKind.DOMAIN}),
        emits=frozenset(),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.OPEN_STANDARD,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=40,
        note="Public hostname infrastructure only; never a subject/device IP lead.",
    ),
    SourceCapability(
        name="wayback_url_availability",
        accepts=frozenset({LeadKind.URL}),
        emits=frozenset(),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=42,
        note=(
            "Internet Archive Wayback capture availability metadata for canonical URLs only; "
            "no archived content fetch, person attribution or emitted leads."
        ),
    ),
    SourceCapability(
        name="stack_overflow_public_profile",
        accepts=frozenset({LeadKind.URL}),
        emits=frozenset(),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=43,
        note=(
            "Official Stack Exchange API metadata for exact Stack Overflow profile URLs only; "
            "attributed account context, no fuzzy search, contact fields or emitted leads."
        ),
    ),
    SourceCapability(
        name="openalex_exact_author",
        accepts=frozenset({LeadKind.URL}),
        emits=frozenset(),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.FREE_TIER,
        credential_class=SourceCredentialClass.FREE_API_KEY,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=44,
        note=(
            "Official OpenAlex singleton author metadata for exact OpenAlex author URLs only; "
            "free API key, no name search, affiliations, work expansion or emitted leads."
        ),
    ),
    SourceCapability(
        name="wikidata_exact_entity",
        accepts=frozenset({LeadKind.URL}),
        emits=frozenset(),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=44,
        note=(
            "Official Wikidata wbgetentities metadata for exact item URLs only; English label/description "
            "only, no entity search, claims expansion, external IDs or emitted leads."
        ),
    ),
    SourceCapability(
        name="rdap_domain_registry",
        accepts=frozenset({LeadKind.DOMAIN}),
        emits=frozenset(),
        status=SourceStatus.ACTIVE,
        mode=SourceMode.OPEN_STANDARD,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=45,
        note=(
            "Authoritative IANA-bootstrap-selected RDAP metadata for explicit DOMAIN seeds only; "
            "emitted subject leads are empty and discovered domains remain display-only."
        ),
    ),
    SourceCapability(
        name="brave_public_web_index",
        accepts=frozenset({LeadKind.USERNAME, LeadKind.EMAIL, LeadKind.PHONE, LeadKind.URL}),
        emits=frozenset(),
        status=SourceStatus.OPTIONAL,
        mode=SourceMode.LICENSED_SEARCH,
        cost_class=SourceCostClass.METERED,
        credential_class=SourceCredentialClass.METERED_API_KEY,
        source_policy_reviewed=True,
        recursive_eligible=True,
        priority=60,
        note="Exact-identifier public-web search; snippets do not become new leads.",
    ),
    SourceCapability(
        name="numverify",
        accepts=frozenset({LeadKind.PHONE}),
        emits=frozenset({LeadKind.LOCATION}),
        status=SourceStatus.REVIEW_REQUIRED,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.UNKNOWN,
        credential_class=SourceCredentialClass.API_KEY_UNKNOWN_COST,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=100,
        note="Existing provider-registry candidate; exact current terms/privacy/cost review required.",
    ),
    SourceCapability(
        name="abstract_phone_intelligence",
        accepts=frozenset({LeadKind.PHONE}),
        emits=frozenset({LeadKind.LOCATION}),
        status=SourceStatus.REVIEW_REQUIRED,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.UNKNOWN,
        credential_class=SourceCredentialClass.API_KEY_UNKNOWN_COST,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=105,
        note="Existing provider-registry candidate; exact current terms/privacy/cost review required.",
    ),
    SourceCapability(
        name="ipqualityscore",
        accepts=frozenset({LeadKind.PHONE}),
        emits=frozenset(),
        status=SourceStatus.REVIEW_REQUIRED,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.UNKNOWN,
        credential_class=SourceCredentialClass.API_KEY_UNKNOWN_COST,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=110,
        note="Phone-risk metadata candidate only after current source-policy/cost review.",
    ),
    SourceCapability(
        name="maigret",
        accepts=frozenset({LeadKind.USERNAME}),
        emits=frozenset({LeadKind.URL}),
        status=SourceStatus.PLANNED,
        mode=SourceMode.GOVERNED_PROVIDER,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=115,
        note="Existing planned username-discovery candidate; no recursion/proxy/autoupdate activation.",
    ),
    SourceCapability(
        name="whatsmyname",
        accepts=frozenset({LeadKind.USERNAME}),
        emits=frozenset({LeadKind.URL}),
        status=SourceStatus.REVIEW_REQUIRED,
        mode=SourceMode.GOVERNED_PROVIDER,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=120,
        note="Dataset/license boundary must be reviewed before executable use.",
    ),
    SourceCapability(
        name="truecaller_manual",
        accepts=frozenset({LeadKind.PHONE}),
        emits=frozenset({LeadKind.NAME}),
        status=SourceStatus.MANUAL_ONLY,
        mode=SourceMode.MANUAL,
        cost_class=SourceCostClass.MANUAL,
        credential_class=SourceCredentialClass.MANUAL,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=125,
        note="Manual-only because lookup visibility/contact risk may exist; never silent recursion.",
    ),
    SourceCapability(
        name="phoneinfoga",
        accepts=frozenset({LeadKind.PHONE}),
        emits=frozenset(),
        status=SourceStatus.REFERENCE_ONLY,
        mode=SourceMode.REFERENCE,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=130,
        note="Reference-only; not executable through the Apache core.",
    ),
    SourceCapability(
        name="gravatar_public_profile",
        accepts=frozenset({LeadKind.EMAIL}),
        emits=frozenset({LeadKind.URL, LeadKind.NAME, LeadKind.ORGANIZATION, LeadKind.LOCATION}),
        status=SourceStatus.PLANNED,
        mode=SourceMode.PUBLIC_API,
        cost_class=SourceCostClass.FREE_TIER,
        credential_class=SourceCredentialClass.FREE_API_KEY,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=145,
        note=(
            "Adapter target: SHA-256 email identifier to public profile data; production "
            "adapter should use a server-side API key."
        ),
    ),
    SourceCapability(
        name="webfinger_activitypub",
        accepts=frozenset({LeadKind.URL}),
        emits=frozenset({LeadKind.URL}),
        status=SourceStatus.PLANNED,
        mode=SourceMode.OPEN_STANDARD,
        cost_class=SourceCostClass.ZERO_DIRECT_COST,
        credential_class=SourceCredentialClass.NONE,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=150,
        note=(
            "Compatibility source key for WebFinger public-link resolution only. ActivityPub actor "
            "fetching is a separate future capability; WebFinger does not emit generic username or "
            "name leads."
        ),
    ),
    SourceCapability(
        name="google_people_authorized",
        accepts=frozenset({LeadKind.EMAIL, LeadKind.PHONE, LeadKind.NAME}),
        emits=frozenset({LeadKind.EMAIL, LeadKind.PHONE, LeadKind.NAME, LeadKind.ORGANIZATION}),
        status=SourceStatus.PLANNED,
        mode=SourceMode.USER_AUTHORIZED,
        cost_class=SourceCostClass.UNKNOWN,
        credential_class=SourceCredentialClass.USER_OAUTH,
        source_policy_reviewed=False,
        recursive_eligible=False,
        priority=160,
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
    include_deferred: bool = False,
    zero_spend_only: bool = False,
    recursive_only: bool = False,
) -> tuple[SourceCapability, ...]:
    """Return deterministic source capabilities that declare support for a lead kind.

    A catalog match is planning metadata only. It never bypasses adapter existence,
    source policy, purpose/consent checks, credentials, budgets or execution gates.
    """

    allowed_statuses = {SourceStatus.ACTIVE}
    if include_optional:
        allowed_statuses.add(SourceStatus.OPTIONAL)
    if include_planned:
        allowed_statuses.add(SourceStatus.PLANNED)
    if include_deferred:
        allowed_statuses.update(
            {
                SourceStatus.REVIEW_REQUIRED,
                SourceStatus.MANUAL_ONLY,
                SourceStatus.REFERENCE_ONLY,
            }
        )

    selected = [
        source
        for source in SOURCE_CATALOG
        if kind in source.accepts
        and source.status in allowed_statuses
        and (not zero_spend_only or source.zero_spend_eligible)
        and (not recursive_only or source.recursive_eligible)
    ]
    return tuple(sorted(selected, key=lambda source: (source.priority, source.name)))
