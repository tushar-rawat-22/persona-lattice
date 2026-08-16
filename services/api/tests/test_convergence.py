# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import defaultdict

import pytest

from app.convergence import MAX_CONVERGENCE_NODES, build_converged_payload, run_converged_research
from app.models import Purpose
from app.research import QuickObservation, QuickResearchReport, ResearchKind


def _report(kind: ResearchKind, value: str, *, details: dict[str, object] | None = None):
    observations = ()
    if details is not None:
        observations = (
            QuickObservation(
                source="synthetic_public_source",
                source_locator=f"https://example.test/{kind.value}/{value}",
                summary="Synthetic public evidence.",
                details=details,
            ),
        )
    return QuickResearchReport(kind=kind, normalized_value=value, observations=observations)


@pytest.mark.asyncio
async def test_convergence_follows_only_allowlisted_public_fields() -> None:
    calls: list[tuple[ResearchKind, str]] = []

    async def runner(*, kind, value, purpose, consent_acknowledged):
        calls.append((kind, value))
        assert purpose is Purpose.PUBLIC_SOURCE_RESEARCH
        assert consent_acknowledged is True
        if kind is ResearchKind.USERNAME and value == "seeduser":
            return _report(
                kind,
                value,
                details={
                    "email": "public@example.test",
                    "twitter_username": "seconduser",
                    "blog": "https://portfolio.example.test",
                    "location": "Bengaluru",
                    "company": "Example Corp",
                    "ip": "203.0.113.10",
                },
            )
        return _report(kind, value)

    result = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="seeduser",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )

    assert {(node.kind, node.report.normalized_value) for node in result.nodes} == {
        (ResearchKind.USERNAME, "seeduser"),
        (ResearchKind.EMAIL, "public@example.test"),
        (ResearchKind.USERNAME, "seconduser"),
        (ResearchKind.URL, "https://portfolio.example.test"),
    }
    assert all("Bengaluru" not in value for _kind, value in calls)
    assert all("203.0.113.10" not in value for _kind, value in calls)
    assert len(result.edges) == 3


@pytest.mark.asyncio
async def test_convergence_deduplicates_identical_public_pivots() -> None:
    counts = defaultdict(int)

    async def runner(*, kind, value, purpose, consent_acknowledged):
        counts[(kind, value)] += 1
        if kind is ResearchKind.USERNAME:
            return QuickResearchReport(
                kind=kind,
                normalized_value=value,
                observations=(
                    QuickObservation(
                        source="one",
                        source_locator="https://one.test",
                        summary="one",
                        details={"email": "same@example.test"},
                    ),
                    QuickObservation(
                        source="two",
                        source_locator="https://two.test",
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

    assert counts[(ResearchKind.EMAIL, "same@example.test")] == 2
    assert len([node for node in result.nodes if node.kind is ResearchKind.EMAIL]) == 1
    assert len(result.edges) == 1


@pytest.mark.asyncio
async def test_convergence_is_bounded_and_reports_truncation() -> None:
    async def runner(*, kind, value, purpose, consent_acknowledged):
        if kind is ResearchKind.USERNAME:
            index = int(value.removeprefix("user") or "0")
            return _report(
                kind,
                value,
                details={"twitter_username": f"user{index + 1}"},
            )
        return _report(kind, value)

    result = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="user0",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
        max_depth=2,
        max_nodes=2,
    )

    assert len(result.nodes) == 2
    assert result.truncated is True


@pytest.mark.asyncio
async def test_converged_payload_never_becomes_identity_probability() -> None:
    async def runner(*, kind, value, purpose, consent_acknowledged):
        return _report(kind, value)

    result = await run_converged_research(
        kind=ResearchKind.EMAIL,
        value="person@example.test",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )
    payload = build_converged_payload(result)

    assert payload["executive_summary"]["identity_probability"] is None
    assert payload["executive_summary"]["identity_claim"] is False
    assert payload["safety_boundary"]["covert_ip_discovery"] is False
    assert payload["safety_boundary"]["max_nodes"] == MAX_CONVERGENCE_NODES
