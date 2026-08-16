# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.convergence import build_converged_payload, run_converged_research
from app.intelligence import FrontierDecision
from app.models import Purpose
from app.research import QuickObservation, QuickResearchReport, ResearchKind


def _report(
    kind: ResearchKind,
    value: str,
    details: dict[str, object] | None = None,
    *,
    source: str = "synthetic_public_source",
    source_locator: str = "https://example.test/profile",
):
    observations = ()
    if details is not None:
        observations = (
            QuickObservation(
                source=source,
                source_locator=source_locator,
                summary="Synthetic public evidence.",
                details=details,
            ),
        )
    return QuickResearchReport(kind=kind, normalized_value=value, observations=observations)


@pytest.mark.asyncio
async def test_convergence_preserves_generic_username_case_in_deduplication() -> None:
    calls: list[tuple[ResearchKind, str]] = []

    async def runner(*, kind, value, purpose, consent_acknowledged):
        calls.append((kind, value))
        if kind is ResearchKind.USERNAME and value == "Seed":
            return _report(
                kind,
                value,
                {
                    "username": "CaseHandle",
                    "twitter_username": "casehandle",
                },
            )
        return _report(kind, value)

    result = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="Seed",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )

    assert (ResearchKind.USERNAME, "CaseHandle") in calls
    assert (ResearchKind.USERNAME, "casehandle") in calls
    assert {node.key for node in result.nodes} >= {
        "username:Seed",
        "username:CaseHandle",
        "username:casehandle",
    }


@pytest.mark.asyncio
async def test_convergence_records_review_display_and_admitted_lead_states() -> None:
    calls: list[tuple[ResearchKind, str]] = []

    async def runner(*, kind, value, purpose, consent_acknowledged):
        calls.append((kind, value))
        if kind is ResearchKind.USERNAME and value == "seed":
            return _report(
                kind,
                value,
                {
                    "public_phone": "+919876543210",
                    "company": "Example Corp",
                    "location": "Bengaluru",
                    "public_email": "safe@example.test",
                },
            )
        return _report(kind, value)

    result = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="seed",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )

    assert (ResearchKind.EMAIL, "safe@example.test") in calls
    assert (ResearchKind.PHONE, "+919876543210") not in calls
    assert all(value != "Example Corp" for _kind, value in calls)
    assert all(value != "Bengaluru" for _kind, value in calls)

    decisions = {(record.candidate.kind.value, record.decision) for record in result.lead_decisions}
    assert ("email", FrontierDecision.ADMITTED) in decisions
    assert ("phone", FrontierDecision.REVIEW_REQUIRED) in decisions
    assert ("organization", FrontierDecision.DISPLAY_ONLY) in decisions
    assert ("location", FrontierDecision.DISPLAY_ONLY) in decisions

    payload = build_converged_payload(result)
    graph = payload["lead_graph"]
    assert graph["policy_version"] == "v2-evidence-lead-policy-v1"
    assert graph["decision_counts"]["admitted"] == 1
    assert graph["decision_counts"]["review_required"] == 1
    assert graph["decision_counts"]["display_only"] == 2


@pytest.mark.asyncio
async def test_convergence_preserves_duplicate_lead_origins_without_duplicate_lookup() -> None:
    calls: list[tuple[ResearchKind, str]] = []

    async def runner(*, kind, value, purpose, consent_acknowledged):
        calls.append((kind, value))
        if kind is ResearchKind.USERNAME:
            return QuickResearchReport(
                kind=kind,
                normalized_value=value,
                observations=(
                    QuickObservation(
                        source="source_one",
                        source_locator="https://one.example.test",
                        summary="one",
                        details={"public_email": "same@example.test"},
                    ),
                    QuickObservation(
                        source="source_two",
                        source_locator="https://two.example.test",
                        summary="two",
                        details={"email": "same@example.test"},
                    ),
                ),
            )
        return _report(kind, value)

    result = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="seed",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )

    assert calls.count((ResearchKind.EMAIL, "same@example.test")) == 1
    same_email_records = [
        record
        for record in result.lead_decisions
        if record.candidate.key == "email:same@example.test"
    ]
    assert len(same_email_records) == 2
    assert {record.candidate.source for record in same_email_records} == {
        "source_one",
        "source_two",
    }
    assert {record.decision for record in same_email_records} == {
        FrontierDecision.ADMITTED,
        FrontierDecision.DUPLICATE,
    }


@pytest.mark.asyncio
async def test_convergence_records_provider_failure_and_releases_frontier_budget() -> None:
    calls: list[tuple[ResearchKind, str]] = []

    async def runner(*, kind, value, purpose, consent_acknowledged):
        calls.append((kind, value))
        if kind is ResearchKind.USERNAME:
            return _report(
                kind,
                value,
                {
                    "public_email": "fail@example.test",
                    "website_url": "https://continue.example.test",
                },
            )
        if kind is ResearchKind.EMAIL:
            raise RuntimeError("synthetic provider failure")
        return _report(kind, value)

    result = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="seed",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
        max_nodes=2,
    )

    assert (ResearchKind.EMAIL, "fail@example.test") in calls
    assert (ResearchKind.URL, "https://continue.example.test") in calls
    assert any(
        record.decision is FrontierDecision.PROVIDER_FAILED
        for record in result.lead_decisions
        if record.candidate.kind.value == "email"
    )
    assert any(node.kind is ResearchKind.URL for node in result.nodes)


@pytest.mark.asyncio
async def test_convergence_reports_blocked_field_names_without_retaining_values() -> None:
    async def runner(*, kind, value, purpose, consent_acknowledged):
        if kind is ResearchKind.USERNAME and value == "seed":
            return _report(
                kind,
                value,
                {
                    "aadhaar_number": "1111-2222-3333",
                    "device_ip": "198.51.100.42",
                },
            )
        return _report(kind, value)

    result = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="seed",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )

    assert result.blocked_field_names == ("aadhaar_number", "device_ip")
    joined = "\n".join(result.warnings)
    assert "aadhaar_number" in joined
    assert "device_ip" in joined
    assert "1111-2222-3333" not in joined
    assert "198.51.100.42" not in joined

    payload = build_converged_payload(result)
    serialized = repr(payload["lead_graph"])
    assert "aadhaar_number" in serialized
    assert "device_ip" in serialized
    assert "1111-2222-3333" not in serialized
    assert "198.51.100.42" not in serialized
