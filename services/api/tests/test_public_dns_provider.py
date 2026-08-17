# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.providers.base import ProviderQuery
from app.providers.errors import ProviderTransientError, ProviderValidationError
from app.providers.public_dns import PublicDnsInfrastructureProvider


def _query(kind: str, value: str) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


@pytest.mark.asyncio
async def test_dns_provider_resolves_only_url_hostname_and_marks_infrastructure() -> None:
    async def resolver(hostname: str) -> tuple[str, ...]:
        assert hostname == "example.com"
        return ("93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946")

    result = await PublicDnsInfrastructureProvider(resolver=resolver).execute(
        _query("url", "https://example.com/path?q=1"),
        None,
    )

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "dns://example.com"
    assert observation.payload == {
        "hostname": "example.com",
        "public_infrastructure_ips": [
            "93.184.216.34",
            "2606:2800:220:1:248:1893:25c8:1946",
        ],
        "personal_device_ip_claim": False,
        "physical_location_claim": False,
    }


@pytest.mark.asyncio
async def test_dns_provider_empty_resolution_is_valid_no_observation() -> None:
    async def resolver(hostname: str) -> tuple[str, ...]:
        return ()

    result = await PublicDnsInfrastructureProvider(resolver=resolver).execute(
        _query("url", "https://missing.example/"),
        None,
    )
    assert result.observations == ()


@pytest.mark.asyncio
async def test_dns_provider_rejects_credentials_non_url_and_credential_bearing_url() -> None:
    async def resolver(hostname: str) -> tuple[str, ...]:
        return ()

    provider = PublicDnsInfrastructureProvider(resolver=resolver)
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query("url", "https://example.com"), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query("domain", "example.com"), None)
    with pytest.raises(ProviderValidationError, match="credential-bearing"):
        await provider.execute(_query("url", "https://user:pass@example.com/"), None)


@pytest.mark.asyncio
async def test_dns_provider_fails_closed_on_non_global_or_excess_resolver_output() -> None:
    async def private_resolver(hostname: str) -> tuple[str, ...]:
        return ("127.0.0.1",)

    with pytest.raises(ProviderValidationError, match="non-global"):
        await PublicDnsInfrastructureProvider(resolver=private_resolver).execute(
            _query("url", "https://example.com"),
            None,
        )

    async def excessive_resolver(hostname: str) -> tuple[str, ...]:
        return tuple(f"8.8.8.{index}" for index in range(1, 10))

    with pytest.raises(ProviderValidationError, match="address limit"):
        await PublicDnsInfrastructureProvider(resolver=excessive_resolver).execute(
            _query("url", "https://example.com"),
            None,
        )


@pytest.mark.asyncio
async def test_dns_provider_maps_resolver_oserror_to_transient_failure() -> None:
    async def resolver(hostname: str) -> tuple[str, ...]:
        raise OSError("resolver unavailable")

    provider = PublicDnsInfrastructureProvider(resolver=resolver)
    with pytest.raises(ProviderTransientError, match="unavailable"):
        await provider.execute(_query("url", "https://example.com"), None)
