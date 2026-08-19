# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.convergence import build_converged_payload, run_converged_research
from app.evidence import IdentifierKind, InvalidIdentifier, normalize_identifier
from app.intelligence import LeadDisposition, LeadKind, extract_observation_leads
from app.intelligence.contracts import canonicalize_lead
from app.intelligence.source_states import SourceRunReason
from app.models import Purpose
from app.providers.rdap_admission import normalize_rdap_domain
from app.providers.rdap_bootstrap_cache import RdapBootstrapUnavailableError
from app.providers.shared_runtime import DEFAULT_RDAP_PROVIDER
from app.research import ResearchKind, run_quick_research


class _UnavailableBootstrapCache:
    async def get_payload(self):
        raise RdapBootstrapUnavailableError("bootstrap unavailable in deterministic test")


def test_domain_uses_one_m1_normalization_authority() -> None:
    normalized = normalize_identifier(IdentifierKind.DOMAIN, "BÜCHER.Example.")
    lead_value, lead_key = canonicalize_lead(LeadKind.DOMAIN, "BÜCHER.Example.")
    rdap_target = normalize_rdap_domain("BÜCHER.Example.")

    assert normalized.normalized_value == "xn--bcher-kva.example"
    assert normalized.comparison_key == "xn--bcher-kva.example"
    assert lead_value == normalized.normalized_value
    assert lead_key == normalized.comparison_key
    assert rdap_target.domain == normalized.normalized_value


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com",
        " example.com ",
        "localhost",
        "127.0.0.1",
        "example.local",
        "bad_label.example",
    ],
)
def test_domain_rejects_ambiguous_or_non_public_seed_shapes(value: str) -> None:
    with pytest.raises(InvalidIdentifier):
        normalize_identifier(IdentifierKind.DOMAIN, value)


@pytest.mark.asyncio
async def test_explicit_domain_seed_is_reachable_when_routing_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(DEFAULT_RDAP_PROVIDER, "bootstrap_cache", _UnavailableBootstrapCache())

    report = await run_quick_research(
        kind=ResearchKind.DOMAIN,
        value="Example.COM.",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
    )

    assert report.kind is ResearchKind.DOMAIN
    assert report.normalized_value == "example.com"
    assert report.observations == ()
    assert len(report.source_runs) == 1
    assert report.source_runs[0].reason is SourceRunReason.ROUTING_UNAVAILABLE
    assert report.source_runs[0].execution_attempted is False


@pytest.mark.asyncio
async def test_domain_seed_survives_convergence_and_ephemeral_m5(monkeypatch) -> None:
    monkeypatch.setattr(DEFAULT_RDAP_PROVIDER, "bootstrap_cache", _UnavailableBootstrapCache())

    report = await run_converged_research(
        kind=ResearchKind.DOMAIN,
        value="Example.COM.",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
    )
    payload = build_converged_payload(report)

    assert report.seed_kind is ResearchKind.DOMAIN
    assert report.seed_value == "example.com"
    assert len(report.nodes) == 1
    assert report.edges == ()
    assert payload["m5"]["identifier_count"] == 1
    assert payload["m5"]["observation_count"] == 0
    assert payload["m5"]["candidate_count"] == 0
    assert payload["m5"]["is_identity_claim"] is False


def test_discovered_domain_remains_display_only() -> None:
    extraction = extract_observation_leads(
        details={"domain": "Example.COM."},
        source="synthetic_public_source",
        source_locator="https://example.test/evidence",
    )

    assert len(extraction.candidates) == 1
    candidate = extraction.candidates[0]
    assert candidate.kind is LeadKind.DOMAIN
    assert candidate.value == "example.com"
    assert candidate.disposition is LeadDisposition.DISPLAY_ONLY
