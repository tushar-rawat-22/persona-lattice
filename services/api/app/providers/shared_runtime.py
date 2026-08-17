# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .github_public import GitHubPublicProfileProvider
from .gitlab_public import GitLabPublicProfileProvider
from .runtime import ProviderRuntime
from .sherlock import SherlockProvider


# Production quick-research providers share one process-wide runtime so provider
# rate/concurrency state cannot fragment as individual sources migrate off the
# frozen legacy research boundary.
DEFAULT_SHERLOCK_PROVIDER = SherlockProvider()
DEFAULT_GITHUB_PROVIDER = GitHubPublicProfileProvider()
DEFAULT_GITLAB_PROVIDER = GitLabPublicProfileProvider()
DEFAULT_PROVIDER_RUNTIME = ProviderRuntime(
    adapters=[
        DEFAULT_SHERLOCK_PROVIDER,
        DEFAULT_GITHUB_PROVIDER,
        DEFAULT_GITLAB_PROVIDER,
    ]
)


def default_provider(name: str):
    """Return the process-owned production adapter registered under ``name``.

    This helper intentionally exposes the exact adapter instance owned by the
    shared runtime rather than constructing a replacement with fresh budgets.
    """

    return DEFAULT_PROVIDER_RUNTIME.adapters.get(name)
