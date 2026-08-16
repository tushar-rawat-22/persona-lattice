# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.models import Purpose
from app.public_search import PublicSearchResult
from app.research import ResearchKind, run_quick_research


async def _search(identifier: str) -> tuple[PublicSearchResult, ...]:
    return (
        PublicSearchResult(
            title=f"Public mention of {identifier}",
            url="https://public.example.test/mention",
            description="Indexed public page snippet.",
        ),
    )


async def _none_profile(_value: str):
    return None


async def _network(_hostname: str) -> tuple[str, ...]:
    return ("203.0.113.8",)


@pytest.mark.asyncio
async def test_email_research_adds_exact_public_index_evidence_without_owner_claim() -> None:
    report = await run_quick_research(
        kind=ResearchKind.EMAIL,
        value="person@example.test",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
        gitlab_email_lookup=_none_profile,
        public_search_lookup=_search,
    )

    indexed = next(item for item in report.observations if item.source == "brave_public_web_index")
    assert indexed.details["exact_identifier_query"] is True
    assert indexed.details["content_fetched"] is False
    assert indexed.details["identity_claim"] is False


@pytest.mark.asyncio
async def test_phone_research_combines_numbering_metadata_with_public_index_mentions() -> None:
    report = await run_quick_research(
        kind=ResearchKind.PHONE,
        value="+919876543210",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
        public_search_lookup=_search,
    )

    sources = {item.source for item in report.observations}
    assert "libphonenumber_metadata" in sources
    assert "brave_public_web_index" in sources


@pytest.mark.asyncio
async def test_url_research_labels_resolved_ips_as_infrastructure_not_personal_ip() -> None:
    report = await run_quick_research(
        kind=ResearchKind.URL,
        value="https://example.test/profile",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
        public_search_lookup=_search,
        network_lookup=_network,
    )

    dns = next(item for item in report.observations if item.source == "public_dns_infrastructure")
    assert dns.details["public_infrastructure_ips"] == ["203.0.113.8"]
    assert dns.details["personal_device_ip_claim"] is False
    assert dns.details["physical_location_claim"] is False
