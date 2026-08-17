# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.providers.registry import PROVIDER_BY_NAME
from app.providers.shared_runtime import (
    DEFAULT_BRAVE_PROVIDER,
    DEFAULT_CODEFORCES_PROVIDER,
    DEFAULT_DNS_PROVIDER,
    DEFAULT_GITHUB_PROVIDER,
    DEFAULT_GITLAB_PROVIDER,
    DEFAULT_PROVIDER_RUNTIME,
    DEFAULT_SHERLOCK_PROVIDER,
    default_provider,
)


def test_shared_production_runtime_owns_current_governed_quick_research_providers() -> None:
    assert set(DEFAULT_PROVIDER_RUNTIME.adapters) == {
        "sherlock",
        "github_public_api",
        "gitlab_public_api",
        "codeforces_public_api",
        "public_dns_infrastructure",
        "brave_public_web_index",
    }
    assert DEFAULT_PROVIDER_RUNTIME.adapters["sherlock"] is DEFAULT_SHERLOCK_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["github_public_api"] is DEFAULT_GITHUB_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["gitlab_public_api"] is DEFAULT_GITLAB_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["codeforces_public_api"] is DEFAULT_CODEFORCES_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["public_dns_infrastructure"] is DEFAULT_DNS_PROVIDER
    assert DEFAULT_PROVIDER_RUNTIME.adapters["brave_public_web_index"] is DEFAULT_BRAVE_PROVIDER


def test_shared_runtime_adapters_match_reviewed_registry_descriptors() -> None:
    assert DEFAULT_SHERLOCK_PROVIDER.descriptor is PROVIDER_BY_NAME["sherlock"]
    assert DEFAULT_GITHUB_PROVIDER.descriptor is PROVIDER_BY_NAME["github_public_api"]
    assert DEFAULT_GITLAB_PROVIDER.descriptor is PROVIDER_BY_NAME["gitlab_public_api"]
    assert DEFAULT_CODEFORCES_PROVIDER.descriptor is PROVIDER_BY_NAME["codeforces_public_api"]
    assert DEFAULT_DNS_PROVIDER.descriptor is PROVIDER_BY_NAME["public_dns_infrastructure"]
    assert DEFAULT_BRAVE_PROVIDER.descriptor is PROVIDER_BY_NAME["brave_public_web_index"]


def test_default_provider_returns_process_owned_adapter_without_reinstantiation() -> None:
    assert default_provider("sherlock") is DEFAULT_SHERLOCK_PROVIDER
    assert default_provider("github_public_api") is DEFAULT_GITHUB_PROVIDER
    assert default_provider("gitlab_public_api") is DEFAULT_GITLAB_PROVIDER
    assert default_provider("codeforces_public_api") is DEFAULT_CODEFORCES_PROVIDER
    assert default_provider("public_dns_infrastructure") is DEFAULT_DNS_PROVIDER
    assert default_provider("brave_public_web_index") is DEFAULT_BRAVE_PROVIDER
    assert default_provider("not-registered") is None
