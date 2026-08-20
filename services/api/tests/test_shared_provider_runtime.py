# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.providers.registry import PROVIDER_BY_NAME
from app.providers.shared_runtime import (
    DEFAULT_BLUESKY_PROVIDER,
    DEFAULT_BRAVE_PROVIDER,
    DEFAULT_CODEFORCES_PROVIDER,
    DEFAULT_DNS_PROVIDER,
    DEFAULT_GITHUB_PROVIDER,
    DEFAULT_GITLAB_PROVIDER,
    DEFAULT_OPENALEX_PROVIDER,
    DEFAULT_PROVIDER_RUNTIME,
    DEFAULT_RDAP_PROVIDER,
    DEFAULT_SHERLOCK_PROVIDER,
    DEFAULT_STACK_OVERFLOW_PROVIDER,
    DEFAULT_WAYBACK_PROVIDER,
    default_provider,
)


def test_shared_production_runtime_owns_current_governed_quick_research_providers() -> None:
    assert set(DEFAULT_PROVIDER_RUNTIME.adapters) == {
        "sherlock",
        "github_public_api",
        "gitlab_public_api",
        "codeforces_public_api",
        "bluesky_public_profile",
        "public_dns_infrastructure",
        "wayback_url_availability",
        "stack_overflow_public_profile",
        "openalex_exact_author",
        "rdap_domain_registry",
        "brave_public_web_index",
    }
    assert DEFAULT_PROVIDER_RUNTIME.adapters["sherlock"] is DEFAULT_SHERLOCK_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["github_public_api"] is DEFAULT_GITHUB_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["gitlab_public_api"] is DEFAULT_GITLAB_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["codeforces_public_api"] is DEFAULT_CODEFORCES_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["bluesky_public_profile"] is DEFAULT_BLUESKY_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["public_dns_infrastructure"] is DEFAULT_DNS_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["wayback_url_availability"] is DEFAULT_WAYBACK_PROVIDER
    assert (
        DEFAULT_PROVIDER_RUNTIME.adapters["stack_overflow_public_profile"]
        is DEFAULT_STACK_OVERFLOW_PROVIDER
    )
    assert DEFAULT_PROVIDER_RUNTIME.adapters["openalex_exact_author"] is DEFAULT_OPENALEX_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["rdap_domain_registry"] is DEFAULT_RDAP_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["brave_public_web_index"] is DEFAULT_BRAVE_PROVIDER


def test_shared_runtime_adapters_match_reviewed_registry_descriptors() -> None:
    assert DEFAULT_SHERLOCK_PROVIDER.descriptor is PROVIDER_BY_NAME["sherlock"]
    assert DEFAULT_GITHUB_PROVIDER.descriptor is PROVIDER_BY_NAME["github_public_api"]
    assert DEFAULT_GITLAB_PROVIDER.descriptor is PROVIDER_BY_NAME["gitlab_public_api"]
    assert DEFAULT_CODEFORCES_PROVIDER.descriptor is PROVIDER_BY_NAME["codeforces_public_api"]
    assert DEFAULT_BLUESKY_PROVIDER.descriptor is PROVIDER_BY_NAME["bluesky_public_profile"]
    assert DEFAULT_DNS_PROVIDER.descriptor is PROVIDER_BY_NAME["public_dns_infrastructure"]
    assert DEFAULT_WAYBACK_PROVIDER.descriptor is PROVIDER_BY_NAME["wayback_url_availability"]
    assert DEFAULT_STACK_OVERFLOW_PROVIDER.descriptor is PROVIDER_BY_NAME["stack_overflow_public_profile"]
    assert DEFAULT_OPENALEX_PROVIDER.descriptor is PROVIDER_BY_NAME["openalex_exact_author"]
    assert DEFAULT_RDAP_PROVIDER.descriptor is PROVIDER_BY_NAME["rdap_domain_registry"]
    assert DEFAULT_BRAVE_PROVIDER.descriptor is PROVIDER_BY_NAME["brave_public_web_index"]


def test_default_provider_returns_process_owned_adapter_without_reinstantiation() -> None:
    assert default_provider("sherlock") is DEFAULT_SHERLOCK_PROVIDER
    assert default_provider("github_public_api") is DEFAULT_GITHUB_PROVIDER
    assert default_provider("gitlab_public_api") is DEFAULT_GITLAB_PROVIDER
    assert default_provider("codeforces_public_api") is DEFAULT_CODEFORCES_PROVIDER
    assert default_provider("bluesky_public_profile") is DEFAULT_BLUESKY_PROVIDER
    assert default_provider("public_dns_infrastructure") is DEFAULT_DNS_PROVIDER
    assert default_provider("wayback_url_availability") is DEFAULT_WAYBACK_PROVIDER
    assert default_provider("stack_overflow_public_profile") is DEFAULT_STACK_OVERFLOW_PROVIDER
    assert default_provider("openalex_exact_author") is DEFAULT_OPENALEX_PROVIDER
    assert default_provider("rdap_domain_registry") is DEFAULT_RDAP_PROVIDER
    assert default_provider("brave_public_web_index") is DEFAULT_BRAVE_PROVIDER
    assert default_provider("not-registered") is None
