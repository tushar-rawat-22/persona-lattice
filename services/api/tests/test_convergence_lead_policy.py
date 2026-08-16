# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.convergence import run_converged_research
from app.models import Purpose
from app.research import QuickObservation, QuickResearchReport, ResearchKind


def _report(kind: ResearchKind, value: str, details: dict[str, object] | None = None):
    observations = ()
    if details is not None:
        observations = (
            QuickObservation(
                source="synthetic_public_source",
                source_locator="https://example.test/profile",
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
async def test_convergence_never_executes_review_only_or_display_only_leads() -> None:
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

    await run_converged_research(
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

    joined = "\n".join(result.warnings)
    assert "aadhaar_number" in joined
    assert "device_ip" in joined
    assert "1111-2222-3333" not in joined
    assert "198.51.100.42" not in joined
