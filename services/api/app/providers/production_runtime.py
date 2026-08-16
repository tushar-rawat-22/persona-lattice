# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .base import Provider
from .github_public import GitHubPublicProfileProvider
from .runtime import ProviderRuntime
from .sherlock import SherlockProvider


# One process-wide runtime owns provider-local concurrency and rate budgets for
# every currently governed live-research adapter. New providers must not create a
# parallel module-level runtime in research.py; they join this registry only after
# catalog, binding, descriptor, adapter and source-policy review all agree.
_PRODUCTION_ADAPTERS: tuple[Provider, ...] = (
    SherlockProvider(),
    GitHubPublicProfileProvider(),
)

PRODUCTION_PROVIDER_ADAPTER_BY_NAME: dict[str, Provider] = {
    adapter.descriptor.name: adapter for adapter in _PRODUCTION_ADAPTERS
}
if len(PRODUCTION_PROVIDER_ADAPTER_BY_NAME) != len(_PRODUCTION_ADAPTERS):
    raise RuntimeError("Production provider adapter names must be unique.")

PRODUCTION_PROVIDER_RUNTIME = ProviderRuntime(adapters=list(_PRODUCTION_ADAPTERS))


def production_provider_adapter(name: str) -> Provider:
    try:
        return PRODUCTION_PROVIDER_ADAPTER_BY_NAME[name]
    except KeyError as exc:
        raise KeyError(f"No production provider adapter is registered for {name!r}.") from exc
