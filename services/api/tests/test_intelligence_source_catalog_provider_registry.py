# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.registry import PROVIDER_BY_NAME


GITHUB_UNAUTHENTICATED_PRIMARY_LIMIT_PER_HOUR = 60
CODEFORCES_MINIMUM_REQUEST_INTERVAL_SECONDS = 2.0


def test_existing_non_synthetic_provider_registry_entries_are_catalogued() -> None:
    expected = set(PROVIDER_BY_NAME).difference({"synthetic_echo"})
    assert expected.issubset(SOURCE_BY_NAME)


def test_deferred_provider_registry_entries_are_not_recursive_sources() -> None:
    for name in (
        "numverify",
        "abstract_phone_intelligence",
        "ipqualityscore",
        "maigret",
        "whatsmyname",
        "truecaller_manual",
        "phoneinfoga",
    ):
        source = SOURCE_BY_NAME[name]
        assert source.recursive_eligible is False
        assert source.status in {
            SourceStatus.REVIEW_REQUIRED,
            SourceStatus.PLANNED,
            SourceStatus.MANUAL_ONLY,
            SourceStatus.REFERENCE_ONLY,
        }


def test_governed_registry_providers_currently_recursive_are_explicit() -> None:
    recursive_registry_sources = {
        name
        for name in PROVIDER_BY_NAME
        if name in SOURCE_BY_NAME and SOURCE_BY_NAME[name].recursive_eligible
    }
    assert recursive_registry_sources == {
        "sherlock",
        "github_public_api",
        "gitlab_public_api",
        "codeforces_public_api",
    }


def test_github_public_api_budget_keeps_hourly_headroom() -> None:
    descriptor = PROVIDER_BY_NAME["github_public_api"]
    assert descriptor.rate_window_seconds == 3600.0
    assert descriptor.rate_limit == 50
    assert descriptor.rate_limit < GITHUB_UNAUTHENTICATED_PRIMARY_LIMIT_PER_HOUR


def test_gitlab_public_api_keeps_the_existing_conservative_local_budget() -> None:
    descriptor = PROVIDER_BY_NAME["gitlab_public_api"]
    assert descriptor.rate_window_seconds == 60.0
    assert descriptor.rate_limit == 20
    assert descriptor.supported_identifier_kinds == frozenset({"username", "email"})


def test_codeforces_budget_matches_documented_minimum_request_interval() -> None:
    descriptor = PROVIDER_BY_NAME["codeforces_public_api"]
    assert descriptor.rate_limit == 1
    assert descriptor.rate_window_seconds == CODEFORCES_MINIMUM_REQUEST_INTERVAL_SECONDS
    assert descriptor.max_concurrency == 1
    assert descriptor.supported_identifier_kinds == frozenset({"username"})
