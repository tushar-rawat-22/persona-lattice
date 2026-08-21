# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .bluesky_public import BlueskyPublicProfileProvider
from .brave_search import BravePublicWebSearchProvider
from .codeforces_public import CodeforcesPublicProfileProvider
from .crossref_work import CrossrefExactWorkProvider
from .datacite_doi import DataCiteExactDoiProvider
from .dblp_person import DblpExactPersonProvider
from .github_public import GitHubPublicProfileProvider
from .gitlab_public import GitLabPublicProfileProvider
from .keybase_public import KeybasePublicUserProvider
from .openalex_author import OpenAlexExactAuthorProvider
from .public_dns import PublicDnsInfrastructureProvider
from .rdap_domain import RdapDomainRegistryProvider
from .ror_organization import RorExactOrganizationProvider
from .runtime import ProviderRuntime
from .sherlock import SherlockProvider
from .stack_overflow_public import StackOverflowPublicProfileProvider
from .wayback_availability import WaybackAvailabilityProvider
from .wikidata_entity import WikidataExactEntityProvider


# Production quick-research providers share one process-wide runtime so provider
# rate/concurrency state cannot fragment across request paths.
DEFAULT_SHERLOCK_PROVIDER = SherlockProvider()
DEFAULT_GITHUB_PROVIDER = GitHubPublicProfileProvider()
DEFAULT_GITLAB_PROVIDER = GitLabPublicProfileProvider()
DEFAULT_CODEFORCES_PROVIDER = CodeforcesPublicProfileProvider()
DEFAULT_BLUESKY_PROVIDER = BlueskyPublicProfileProvider()
DEFAULT_KEYBASE_PROVIDER = KeybasePublicUserProvider()
DEFAULT_DNS_PROVIDER = PublicDnsInfrastructureProvider()
DEFAULT_WAYBACK_PROVIDER = WaybackAvailabilityProvider()
DEFAULT_STACK_OVERFLOW_PROVIDER = StackOverflowPublicProfileProvider()
DEFAULT_OPENALEX_PROVIDER = OpenAlexExactAuthorProvider()
DEFAULT_WIKIDATA_PROVIDER = WikidataExactEntityProvider()
DEFAULT_ROR_PROVIDER = RorExactOrganizationProvider()
DEFAULT_DBLP_PROVIDER = DblpExactPersonProvider()
DEFAULT_CROSSREF_PROVIDER = CrossrefExactWorkProvider()
DEFAULT_DATACITE_PROVIDER = DataCiteExactDoiProvider()
DEFAULT_RDAP_PROVIDER = RdapDomainRegistryProvider()
DEFAULT_BRAVE_PROVIDER = BravePublicWebSearchProvider()
DEFAULT_PROVIDER_RUNTIME = ProviderRuntime(
    adapters=[
        DEFAULT_SHERLOCK_PROVIDER,
        DEFAULT_GITHUB_PROVIDER,
        DEFAULT_GITLAB_PROVIDER,
        DEFAULT_CODEFORCES_PROVIDER,
        DEFAULT_BLUESKY_PROVIDER,
        DEFAULT_KEYBASE_PROVIDER,
        DEFAULT_DNS_PROVIDER,
        DEFAULT_WAYBACK_PROVIDER,
        DEFAULT_STACK_OVERFLOW_PROVIDER,
        DEFAULT_OPENALEX_PROVIDER,
        DEFAULT_WIKIDATA_PROVIDER,
        DEFAULT_ROR_PROVIDER,
        DEFAULT_DBLP_PROVIDER,
        DEFAULT_CROSSREF_PROVIDER,
        DEFAULT_DATACITE_PROVIDER,
        DEFAULT_RDAP_PROVIDER,
        DEFAULT_BRAVE_PROVIDER,
    ]
)


def default_provider(name: str):
    """Return the process-owned production adapter registered under ``name``.

    This helper intentionally exposes the exact adapter instance owned by the
    shared runtime rather than constructing a replacement with fresh budgets.
    """

    return DEFAULT_PROVIDER_RUNTIME.adapters.get(name)
