# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.contracts import LeadKind
from app.intelligence.source_catalog import SourceStatus
from app.intelligence.source_planner import build_source_plan


def _names(items) -> tuple[str, ...]:
    return tuple(item.name for item in items)


def test_username_plan_separates_current_optional_deferred_and_future_sources() -> None:
    plan = build_source_plan(LeadKind.USERNAME)

    assert "sherlock" in _names(plan.active)
    assert "github_public_api" in _names(plan.active)
    assert "gitlab_public_api" in _names(plan.active)
    assert "codeforces_public_api" in _names(plan.active)
    assert "brave_public_web_index" in _names(plan.optional)
    assert "whatsmyname" in _names(plan.deferred)
    assert "maigret" in _names(plan.planned)
    assert "bluesky_public_profile" in _names(plan.planned)
    assert all(source.status is SourceStatus.PLANNED for source in plan.planned)


def test_phone_plan_exposes_review_and_manual_sources_without_execution_authority() -> None:
    plan = build_source_plan(LeadKind.PHONE)

    assert "libphonenumber_metadata" in _names(plan.active)
    assert "numverify" in _names(plan.deferred)
    assert "abstract_phone_intelligence" in _names(plan.deferred)
    assert "ipqualityscore" in _names(plan.deferred)
    assert "truecaller_manual" in _names(plan.deferred)
    assert "phoneinfoga" in _names(plan.deferred)
    assert all(source.recursive_eligible is False for source in plan.deferred)


def test_zero_spend_plan_moves_metered_sources_out_of_current_plan() -> None:
    plan = build_source_plan(LeadKind.USERNAME, zero_spend_only=True)

    assert "brave_public_web_index" not in _names(plan.optional)
    assert "brave_public_web_index" in _names(plan.excluded_by_budget)
    assert plan.has_zero_spend_current_coverage is True


def test_planned_source_is_never_promoted_by_zero_spend_filter() -> None:
    plan = build_source_plan(LeadKind.EMAIL, zero_spend_only=True)

    assert "gravatar_public_profile" in _names(plan.planned)
    assert "gravatar_public_profile" not in _names(plan.active)
    assert "gravatar_public_profile" not in _names(plan.optional)


def test_domain_plan_exposes_current_dns_and_future_rdap_separately() -> None:
    plan = build_source_plan(LeadKind.DOMAIN)

    assert _names(plan.active) == ("public_dns_infrastructure",)
    assert "rdap_domain_registry" in _names(plan.planned)
    assert plan.has_current_coverage is True


def test_name_has_no_public_recursive_source_but_future_authorized_import_is_visible() -> None:
    plan = build_source_plan(LeadKind.NAME)

    assert plan.active == ()
    assert plan.optional == ()
    assert "google_people_authorized" in _names(plan.planned)
    assert plan.has_current_coverage is False
