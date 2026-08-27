# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.base import AuthMode, ProviderStatus
from app.providers.registry import PROVIDER_BY_NAME


GITHUB_UNAUTHENTICATED_PRIMARY_LIMIT_PER_HOUR = 60
CODEFORCES_MINIMUM_REQUEST_INTERVAL_SECONDS = 2.0


def test_existing_non_synthetic_provider_registry_entries_are_catalogued() -> None:
    expected = set(PROVIDER_BY_NAME).difference({"synthetic_echo"})
    assert expected.issubset(SOURCE_BY_NAME)


def test_deferred_provider_registry_entries_are_not_recursive_sources() -> None:
    for name in (
        "codeforces_public_api",
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
        "keybase_public_user",
        "gitlab_public_api",
        "bluesky_public_profile",
        "public_dns_infrastructure",
        "wayback_url_availability",
        "stack_overflow_public_profile",
        "openalex_exact_author",
        "wikidata_exact_entity",
        "zenodo_exact_record",
        "ror_exact_organization",
        "companies_house_exact_company",
        "dblp_exact_person",
        "crossref_exact_work",
        "datacite_exact_doi",
        "gleif_exact_lei",
        "sec_edgar_exact_cik",
        "rdap_domain_registry",
        "brave_public_web_index",
    }


def test_github_public_api_budget_keeps_hourly_headroom() -> None:
    descriptor = PROVIDER_BY_NAME["github_public_api"]
    assert descriptor.rate_window_seconds == 3600.0
    assert descriptor.rate_limit == 50
    assert descriptor.rate_limit < GITHUB_UNAUTHENTICATED_PRIMARY_LIMIT_PER_HOUR


def test_keybase_is_zero_spend_credentialless_basics_only_and_username_only() -> None:
    descriptor = PROVIDER_BY_NAME["keybase_public_user"]
    capability = SOURCE_BY_NAME["keybase_public_user"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"username"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 16 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 20
    assert descriptor.rate_window_seconds == 60.0


def test_gitlab_public_api_keeps_the_existing_conservative_local_budget() -> None:
    descriptor = PROVIDER_BY_NAME["gitlab_public_api"]
    assert descriptor.rate_window_seconds == 60.0
    assert descriptor.rate_limit == 20
    assert descriptor.supported_identifier_kinds == frozenset({"username", "email", "url"})


def test_codeforces_remains_bounded_but_is_not_executable_while_review_required() -> None:
    descriptor = PROVIDER_BY_NAME["codeforces_public_api"]
    capability = SOURCE_BY_NAME["codeforces_public_api"]
    assert descriptor.status == ProviderStatus.REVIEW_REQUIRED.value
    assert capability.status is SourceStatus.REVIEW_REQUIRED
    assert capability.recursive_eligible is False
    assert descriptor.rate_limit == 1
    assert descriptor.rate_window_seconds == CODEFORCES_MINIMUM_REQUEST_INTERVAL_SECONDS
    assert descriptor.max_concurrency == 1
    assert descriptor.supported_identifier_kinds == frozenset({"username"})


def test_bluesky_is_zero_spend_credentialless_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]
    capability = SOURCE_BY_NAME["bluesky_public_profile"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"username", "url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 64 * 1024
    assert descriptor.max_concurrency == 2
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0


def test_public_dns_policy_is_bounded_and_url_only() -> None:
    descriptor = PROVIDER_BY_NAME["public_dns_infrastructure"]
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 16 * 1024
    assert descriptor.max_concurrency == 2
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0


def test_wayback_is_zero_spend_credentialless_metadata_only_and_url_only() -> None:
    descriptor = PROVIDER_BY_NAME["wayback_url_availability"]
    capability = SOURCE_BY_NAME["wayback_url_availability"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 15
    assert descriptor.rate_window_seconds == 60.0


def test_stack_overflow_is_zero_spend_exact_url_only_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["stack_overflow_public_profile"]
    capability = SOURCE_BY_NAME["stack_overflow_public_profile"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 20
    assert descriptor.rate_window_seconds == 60.0


def test_openalex_is_zero_spend_exact_url_only_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["openalex_exact_author"]
    capability = SOURCE_BY_NAME["openalex_exact_author"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.API_KEY
    assert descriptor.secret_env == "OPENALEX_API_KEY"
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 20
    assert descriptor.rate_window_seconds == 60.0


def test_wikidata_is_zero_spend_exact_url_only_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["wikidata_exact_entity"]
    capability = SOURCE_BY_NAME["wikidata_exact_entity"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0


def test_zenodo_is_zero_spend_exact_url_only_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["zenodo_exact_record"]
    capability = SOURCE_BY_NAME["zenodo_exact_record"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0


def test_ror_is_zero_spend_exact_url_only_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["ror_exact_organization"]
    capability = SOURCE_BY_NAME["ror_exact_organization"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 8
    assert descriptor.rate_window_seconds == 60.0


def test_companies_house_is_zero_spend_exact_url_only_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["companies_house_exact_company"]
    capability = SOURCE_BY_NAME["companies_house_exact_company"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.API_KEY
    assert descriptor.secret_env == "COMPANIES_HOUSE_API_KEY"
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0


def test_dblp_is_zero_spend_exact_url_only_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["dblp_exact_person"]
    capability = SOURCE_BY_NAME["dblp_exact_person"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 6
    assert descriptor.rate_window_seconds == 60.0


def test_crossref_is_zero_spend_exact_url_only_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["crossref_exact_work"]
    capability = SOURCE_BY_NAME["crossref_exact_work"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0


def test_datacite_is_zero_spend_exact_url_fallback_and_locally_bounded() -> None:
    descriptor = PROVIDER_BY_NAME["datacite_exact_doi"]
    capability = SOURCE_BY_NAME["datacite_exact_doi"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 4.0
    assert descriptor.max_response_bytes == 32 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 30
    assert descriptor.rate_window_seconds == 60.0


def test_rdap_is_zero_spend_credentialless_and_domain_only() -> None:
    descriptor = PROVIDER_BY_NAME["rdap_domain_registry"]
    capability = SOURCE_BY_NAME["rdap_domain_registry"]
    assert capability.status is SourceStatus.ACTIVE
    assert capability.zero_spend_eligible is True
    assert capability.emits == frozenset()
    assert descriptor.auth_mode is AuthMode.NONE
    assert descriptor.supported_identifier_kinds == frozenset({"domain"})
    assert descriptor.max_attempts == 1
    assert descriptor.max_response_bytes == 64 * 1024
    assert descriptor.max_concurrency == 2
    assert descriptor.rate_limit == 10
    assert descriptor.rate_window_seconds == 60.0


def test_brave_remains_optional_metered_and_preserves_existing_local_budget() -> None:
    descriptor = PROVIDER_BY_NAME["brave_public_web_index"]
    capability = SOURCE_BY_NAME["brave_public_web_index"]
    assert capability.status is SourceStatus.OPTIONAL
    assert capability.zero_spend_eligible is False
    assert descriptor.auth_mode is AuthMode.API_KEY
    assert descriptor.secret_env == "BRAVE_SEARCH_API_KEY"
    assert descriptor.supported_identifier_kinds == frozenset({"username", "email", "phone", "url"})
    assert descriptor.max_attempts == 1
    assert descriptor.timeout_seconds == 5.0
    assert descriptor.max_response_bytes == 256 * 1024
    assert descriptor.max_concurrency == 1
    assert descriptor.rate_limit == 10
    assert descriptor.rate_window_seconds == 60.0
