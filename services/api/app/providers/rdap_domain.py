# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .errors import (
    ProviderResultValidationError,
    ProviderRoutingUnavailableError,
    ProviderValidationError,
)
from .rdap_admission import RdapAdmissionError, admitted_rdap_domain_observation, normalize_rdap_domain
from .rdap_bootstrap_cache import (
    IANA_RDAP_BOOTSTRAP_CACHE,
    IanaRdapBootstrapCache,
    RdapBootstrapUnavailableError,
    RdapBootstrapValidationError,
)
from .rdap_transport import RdapDomainFetchResult, fetch_rdap_domain
from .registry import PROVIDER_BY_NAME


RdapFetcher = Callable[..., Awaitable[RdapDomainFetchResult | None]]


class RdapDomainRegistryProvider:
    """Metadata-only domain registration lookup through authoritative RDAP services."""

    descriptor = PROVIDER_BY_NAME["rdap_domain_registry"]

    def __init__(
        self,
        *,
        bootstrap_cache: IanaRdapBootstrapCache = IANA_RDAP_BOOTSTRAP_CACHE,
        fetcher: RdapFetcher = fetch_rdap_domain,
    ) -> None:
        self.bootstrap_cache = bootstrap_cache
        self.fetcher = fetcher

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("RDAP does not accept provider credentials.")
        if query.identifier_kind != "domain":
            raise ProviderValidationError("RDAP accepts domain identifiers only.")
        try:
            target = normalize_rdap_domain(query.identifier_value)
        except RdapAdmissionError as exc:
            raise ProviderValidationError("RDAP domain query failed admission.") from exc

        try:
            bootstrap_payload: Mapping[str, object] = await self.bootstrap_cache.get_payload()
        except (RdapBootstrapUnavailableError, RdapBootstrapValidationError) as exc:
            # The authoritative subject provider has not been selected or contacted.
            raise ProviderRoutingUnavailableError(
                "IANA RDAP routing authority is unavailable."
            ) from exc

        result = await self.fetcher(target.domain, bootstrap_payload=bootstrap_payload)
        if result is None:
            return ProviderResult(observations=())

        try:
            admitted = admitted_rdap_domain_observation(
                result.payload,
                requested_domain=target.domain,
                canonical_query_url=result.canonical_query_url,
                source_locator=result.response_url,
            )
        except RdapAdmissionError as exc:
            # A subject provider returned a response; malformed/mismatched data is
            # therefore an attempted provider result, not a pre-call policy block.
            raise ProviderResultValidationError(
                "RDAP provider result failed metadata admission."
            ) from exc

        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=admitted.source_locator,
                    payload=dict(admitted.details),
                ),
            )
        )
