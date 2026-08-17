# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from ..network_metadata import resolve_public_host_ips
from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .errors import ProviderTransientError, ProviderValidationError
from .registry import PROVIDER_BY_NAME


DnsResolver = Callable[[str], Awaitable[tuple[str, ...]]]


def _validated_hostname(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ProviderValidationError("Public DNS infrastructure lookup requires an HTTP(S) URL.")
    if parts.username is not None or parts.password is not None:
        raise ProviderValidationError("Public DNS infrastructure lookup rejects credential-bearing URLs.")
    return parts.hostname.rstrip(".").casefold()


class PublicDnsInfrastructureProvider:
    descriptor = PROVIDER_BY_NAME["public_dns_infrastructure"]

    def __init__(self, *, resolver: DnsResolver = resolve_public_host_ips) -> None:
        self.resolver = resolver

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Public DNS infrastructure lookup does not accept credentials.")
        if query.identifier_kind != "url":
            raise ProviderValidationError("Public DNS infrastructure lookup only accepts URLs.")

        hostname = _validated_hostname(query.identifier_value)
        try:
            public_ips = await self.resolver(hostname)
        except OSError as exc:
            raise ProviderTransientError("Public DNS infrastructure lookup was unavailable.") from exc

        if not public_ips:
            return ProviderResult(observations=())

        return ProviderResult(
            observations=(
                ProviderObservationData(
                    source_locator=f"dns://{hostname}",
                    payload={
                        "hostname": hostname,
                        "public_infrastructure_ips": list(public_ips),
                        "personal_device_ip_claim": False,
                        "physical_location_claim": False,
                    },
                ),
            )
        )
