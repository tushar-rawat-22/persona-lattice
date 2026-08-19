# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.intelligence import LeadKind
from app.intelligence.source_outcomes import source_provider_exception_record
from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.models import Purpose
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResultValidationError,
    ProviderRoutingUnavailableError,
    ProviderTransientError,
)
from app.providers.rdap_bootstrap_cache import RdapBootstrapUnavailableError
from app.providers.rdap_domain import RdapDomainRegistryProvider
from app.providers.rdap_transport import RdapDomainFetchResult
from app.providers.shared_runtime import DEFAULT_PROVIDER_RUNTIME, DEFAULT_RDAP_PROVIDER
from app.research import ResearchKind, run_quick_research


_BOOTSTRAP = {"services": [["com"], ["https://rdap.example/"]]}


class _BootstrapCache:
    def __init__(self, payload=None, error: Exception | None = None):
        self.payload = _BOOTSTRAP if payload is None else payload
        self.error = error

    async def get_payload(self):
        if self.error is not None:
            raise self.error
        return self.payload


def _query(value: str = "example.com") -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind="domain",
        identifier_value=value,
    )


@pytest.mark.asyncio
async def test_rdap_provider_returns_metadata_only_canonical_observation() -> None:
    async def fetcher(domain: str, *, bootstrap_payload):
        assert domain == "example.com"
        assert bootstrap_payload == _BOOTSTRAP
        return RdapDomainFetchResult(
            payload={
                "objectClassName": "domain",
                "ldhName": "example.com",
                "status": ["active"],
                "nameservers": [{"ldhName": "ns1.example.net"}],
                "entities": [
                    {
                        "vcardArray": [
                            "vcard",
                            [["email", {}, "text", "private@example.test"]],
                        ]
                    }
                ],
            },
            canonical_query_url="https://rdap.example/domain/example.com",
            response_url="https://rdap.example/domain/example.com",
        )

    provider = RdapDomainRegistryProvider(
        bootstrap_cache=_BootstrapCache(),
        fetcher=fetcher,
    )
    result = await provider.execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://rdap.example/domain/example.com"
    assert observation.payload == {
        "domain": "example.com",
        "statuses": ("active",),
        "nameservers": ("ns1.example.net",),
        "registration_context": True,
        "identity_claim": False,
        "registrant_contact_retained": False,
        "redaction_authoritative": True,
    }
    assert "entities" not in observation.payload


@pytest.mark.asyncio
async def test_rdap_provider_maps_not_found_to_zero_observations() -> None:
    async def fetcher(domain: str, *, bootstrap_payload):
        return None

    provider = RdapDomainRegistryProvider(
        bootstrap_cache=_BootstrapCache(),
        fetcher=fetcher,
    )
    result = await provider.execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_rdap_bootstrap_failure_is_typed_before_provider_contact() -> None:
    provider = RdapDomainRegistryProvider(
        bootstrap_cache=_BootstrapCache(
            error=RdapBootstrapUnavailableError("bootstrap offline")
        ),
    )

    with pytest.raises(ProviderRoutingUnavailableError) as caught:
        await provider.execute(_query(), None)

    record = source_provider_exception_record(
        source_name="rdap_domain_registry",
        lead_kind=LeadKind.DOMAIN,
        exc=caught.value,
    )
    assert record is not None
    assert record.state is SourceRunState.UNAVAILABLE
    assert record.reason is SourceRunReason.ROUTING_UNAVAILABLE
    assert record.execution_attempted is False


@pytest.mark.asyncio
async def test_rdap_malformed_provider_result_is_attempted_failure() -> None:
    async def fetcher(domain: str, *, bootstrap_payload):
        return RdapDomainFetchResult(
            payload={"objectClassName": "domain", "ldhName": "other.example"},
            canonical_query_url="https://rdap.example/domain/example.com",
            response_url="https://rdap.example/domain/example.com",
        )

    provider = RdapDomainRegistryProvider(
        bootstrap_cache=_BootstrapCache(),
        fetcher=fetcher,
    )
    with pytest.raises(ProviderResultValidationError):
        await provider.execute(_query(), None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_type",
    [ProviderRemoteRateLimitError, ProviderTransientError],
)
async def test_rdap_subject_provider_failures_preserve_attempted_error_type(error_type) -> None:
    async def fetcher(domain: str, *, bootstrap_payload):
        raise error_type("provider failure")

    provider = RdapDomainRegistryProvider(
        bootstrap_cache=_BootstrapCache(),
        fetcher=fetcher,
    )
    with pytest.raises(error_type):
        await provider.execute(_query(), None)


def test_rdap_is_owned_by_process_wide_runtime() -> None:
    assert DEFAULT_PROVIDER_RUNTIME.adapters["rdap_domain_registry"] is DEFAULT_RDAP_PROVIDER


@pytest.mark.asyncio
async def test_domain_quick_research_reports_rdap_success(monkeypatch) -> None:
    async def fetcher(domain: str, *, bootstrap_payload):
        return RdapDomainFetchResult(
            payload={
                "objectClassName": "domain",
                "ldhName": domain,
                "status": [],
                "nameservers": [],
            },
            canonical_query_url=f"https://rdap.example/domain/{domain}",
            response_url=f"https://rdap.example/domain/{domain}",
        )

    monkeypatch.setattr(DEFAULT_RDAP_PROVIDER, "bootstrap_cache", _BootstrapCache())
    monkeypatch.setattr(DEFAULT_RDAP_PROVIDER, "fetcher", fetcher)

    report = await run_quick_research(
        kind=ResearchKind.DOMAIN,
        value="Example.COM.",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
    )

    assert report.normalized_value == "example.com"
    assert len(report.observations) == 1
    assert report.observations[0].source == "rdap_domain_registry"
    assert report.source_runs[0].state is SourceRunState.EXECUTED
    assert report.source_runs[0].observation_count == 1


@pytest.mark.asyncio
async def test_domain_quick_research_reports_bootstrap_failure_as_non_attempt(monkeypatch) -> None:
    monkeypatch.setattr(
        DEFAULT_RDAP_PROVIDER,
        "bootstrap_cache",
        _BootstrapCache(error=RdapBootstrapUnavailableError("bootstrap offline")),
    )

    report = await run_quick_research(
        kind=ResearchKind.DOMAIN,
        value="example.com",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
    )

    assert report.observations == ()
    assert len(report.source_runs) == 1
    assert report.source_runs[0].reason is SourceRunReason.ROUTING_UNAVAILABLE
    assert report.source_runs[0].execution_attempted is False
