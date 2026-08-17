# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.models import Purpose
from app.providers.shared_runtime import DEFAULT_DNS_PROVIDER, default_provider
from app.research import ResearchKind, run_quick_research


async def _no_public_search(_value: str):
    return ()


@pytest.mark.asyncio
async def test_production_url_research_uses_process_owned_dns_adapter(monkeypatch) -> None:
    seen: list[str] = []

    async def resolver(hostname: str) -> tuple[str, ...]:
        seen.append(hostname)
        return ("93.184.216.34",)

    monkeypatch.setattr(DEFAULT_DNS_PROVIDER, "resolver", resolver)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://Example.COM/path?q=1",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
    )

    assert default_provider("public_dns_infrastructure") is DEFAULT_DNS_PROVIDER
    assert seen == ["example.com"]
    dns = [item for item in report.observations if item.source == "public_dns_infrastructure"]
    assert len(dns) == 1
    assert dns[0].source_locator == "dns://example.com"
    assert dns[0].details["public_infrastructure_ips"] == ["93.184.216.34"]
    assert dns[0].details["personal_device_ip_claim"] is False
    assert dns[0].details["physical_location_claim"] is False


@pytest.mark.asyncio
async def test_injected_network_lookup_remains_compatibility_seam(monkeypatch) -> None:
    governed_calls: list[str] = []
    injected_calls: list[str] = []

    async def governed_resolver(hostname: str) -> tuple[str, ...]:
        governed_calls.append(hostname)
        return ("203.0.113.1",)

    async def injected_lookup(hostname: str) -> tuple[str, ...]:
        injected_calls.append(hostname)
        return ("93.184.216.34",)

    monkeypatch.setattr(DEFAULT_DNS_PROVIDER, "resolver", governed_resolver)

    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.com/",
        purpose=Purpose.SELF_AUDIT,
        consent_acknowledged=True,
        public_search_lookup=_no_public_search,
        network_lookup=injected_lookup,
    )

    assert governed_calls == []
    assert injected_calls == ["example.com"]
    dns = [item for item in report.observations if item.source == "public_dns_infrastructure"]
    assert len(dns) == 1
    assert dns[0].details["public_infrastructure_ips"] == ["93.184.216.34"]
