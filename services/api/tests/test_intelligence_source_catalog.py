# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.contracts import LeadKind
from app.intelligence.source_catalog import (
    SOURCE_BY_NAME,
    SOURCE_CATALOG,
    SourceCapability,
    SourceCostClass,
    SourceCredentialClass,
    SourceMode,
    SourceStatus,
    sources_for_lead,
)


def _names(items) -> tuple[str, ...]:
    return tuple(item.name for item in items)


def test_source_catalog_names_are_unique_and_indexed() -> None:
    assert len(SOURCE_BY_NAME) == len(SOURCE_CATALOG)
    assert tuple(SOURCE_BY_NAME) == tuple(source.name for source in SOURCE_CATALOG)


def test_recursive_sources_are_active_or_optional_and_source_policy_reviewed() -> None:
    recursive = [source for source in SOURCE_CATALOG if source.recursive_eligible]
    assert recursive
    assert all(
        source.status in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}
        for source in recursive
    )
    assert all(source.source_policy_reviewed for source in recursive)


def test_planned_sources_are_never_returned_by_recursive_execution_query() -> None:
    for kind in LeadKind:
        selected = sources_for_lead(
            kind,
            include_planned=True,
            recursive_only=True,
        )
        assert all(source.status is not SourceStatus.PLANNED for source in selected)


def test_zero_spend_username_plan_excludes_metered_public_search() -> None:
    selected = sources_for_lead(
        LeadKind.USERNAME,
        include_planned=True,
        zero_spend_only=True,
    )
    names = _names(selected)

    assert "sherlock" in names
    assert "github_public_api" in names
    assert "gitlab_public_api" in names
    assert "codeforces_public_api" in names
    assert "bluesky_public_profile" in names
    assert "brave_public_web_index" not in names


def test_optional_metered_search_requires_metered_api_credential() -> None:
    brave = SOURCE_BY_NAME["brave_public_web_index"]

    assert brave.status is SourceStatus.OPTIONAL
    assert brave.cost_class is SourceCostClass.METERED
    assert brave.credential_class is SourceCredentialClass.METERED_API_KEY
    assert brave.zero_spend_eligible is False


def test_future_email_plan_contains_gravatar_but_not_as_executable() -> None:
    without_planned = sources_for_lead(LeadKind.EMAIL)
    with_planned = sources_for_lead(LeadKind.EMAIL, include_planned=True)

    assert "gravatar_public_profile" not in _names(without_planned)
    assert "gravatar_public_profile" in _names(with_planned)

    gravatar = SOURCE_BY_NAME["gravatar_public_profile"]
    assert gravatar.status is SourceStatus.PLANNED
    assert gravatar.recursive_eligible is False
    assert gravatar.source_policy_reviewed is False
    assert gravatar.credential_class is SourceCredentialClass.FREE_API_KEY


def test_future_domain_plan_contains_rdap_without_promising_unredacted_identity() -> None:
    rdap = SOURCE_BY_NAME["rdap_domain_registry"]

    assert LeadKind.DOMAIN in rdap.accepts
    assert LeadKind.ORGANIZATION in rdap.emits
    assert rdap.status is SourceStatus.PLANNED
    assert rdap.recursive_eligible is False
    assert "actually returns" in rdap.note
    assert "redaction" in rdap.note


def test_public_dns_source_cannot_emit_person_or_personal_ip_leads() -> None:
    dns = SOURCE_BY_NAME["public_dns_infrastructure"]

    assert dns.emits == frozenset()
    assert "never a subject/device IP" in dns.note


def test_user_authorized_source_requires_user_oauth_and_is_not_zero_spend_assumed() -> None:
    google = SOURCE_BY_NAME["google_people_authorized"]

    assert google.mode is SourceMode.USER_AUTHORIZED
    assert google.credential_class is SourceCredentialClass.USER_OAUTH
    assert google.cost_class is SourceCostClass.UNKNOWN
    assert google.zero_spend_eligible is False
    assert google.recursive_eligible is False


def test_source_capability_rejects_unsafe_recursive_planned_source() -> None:
    with pytest.raises(ValueError, match="active or optional"):
        SourceCapability(
            name="unsafe_planned_source",
            accepts=frozenset({LeadKind.USERNAME}),
            emits=frozenset({LeadKind.EMAIL}),
            status=SourceStatus.PLANNED,
            mode=SourceMode.PUBLIC_API,
            cost_class=SourceCostClass.ZERO_DIRECT_COST,
            credential_class=SourceCredentialClass.NONE,
            source_policy_reviewed=True,
            recursive_eligible=True,
        )


def test_source_capability_rejects_unreviewed_recursive_source() -> None:
    with pytest.raises(ValueError, match="reviewed source policy"):
        SourceCapability(
            name="unreviewed_source",
            accepts=frozenset({LeadKind.USERNAME}),
            emits=frozenset({LeadKind.EMAIL}),
            status=SourceStatus.ACTIVE,
            mode=SourceMode.PUBLIC_API,
            cost_class=SourceCostClass.ZERO_DIRECT_COST,
            credential_class=SourceCredentialClass.NONE,
            source_policy_reviewed=False,
            recursive_eligible=True,
        )


def test_source_capability_rejects_metered_source_without_metered_credential() -> None:
    with pytest.raises(ValueError, match="metered API credential"):
        SourceCapability(
            name="bad_metered_source",
            accepts=frozenset({LeadKind.EMAIL}),
            emits=frozenset(),
            status=SourceStatus.OPTIONAL,
            mode=SourceMode.LICENSED_SEARCH,
            cost_class=SourceCostClass.METERED,
            credential_class=SourceCredentialClass.NONE,
            source_policy_reviewed=True,
            recursive_eligible=False,
        )


def test_sources_for_lead_is_deterministically_priority_sorted() -> None:
    selected = sources_for_lead(LeadKind.USERNAME, include_planned=True)
    ordering = [(source.priority, source.name) for source in selected]
    assert ordering == sorted(ordering)
