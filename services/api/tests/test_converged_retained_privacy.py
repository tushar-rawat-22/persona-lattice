# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from app.converged_report import (
    ConvergedReportReferenceError,
    hydrate_case_report_edge_provenance,
    resolve_edge_decision,
)
from app.convergence import (
    ConvergedResearchReport,
    PivotReason,
    ResearchNode,
    build_converged_payload,
    run_converged_research,
)
from app.models import Purpose
from app.research import QuickObservation, QuickResearchReport, ResearchKind


def test_converged_m5_references_canonical_node_observation() -> None:
    locator = "https://gitlab.com/synthetic-user"
    unique_detail = "detail-owned-only-by-canonical-observation"
    observation = QuickObservation(
        source="gitlab_public_api",
        source_locator=locator,
        summary="Synthetic public account candidate.",
        details={
            "account_candidate": True,
            "identity_claim": False,
            "username": "synthetic-user",
            "bio": unique_detail,
        },
    )
    quick = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="synthetic-user",
        observations=(observation,),
    )
    node = ResearchNode(
        kind=ResearchKind.USERNAME,
        value="synthetic-user",
        depth=0,
        parent_key=None,
        pivot_reason=PivotReason.SEED,
        report=quick,
    )
    report = ConvergedResearchReport(
        seed_kind=ResearchKind.USERNAME,
        seed_value="synthetic-user",
        nodes=(node,),
        edges=(),
        warnings=(),
        truncated=False,
    )

    payload = build_converged_payload(report)
    serialized = json.dumps(payload, sort_keys=True)
    evaluation = payload["m5"]["evaluations"][0]

    assert serialized.count(unique_detail) == 1
    assert serialized.count(locator) == 1
    assert evaluation["candidate_node"] == node.key
    assert evaluation["candidate_observation_index"] == 0
    assert "candidate_source" not in evaluation
    assert "candidate_source_locator" not in evaluation


@pytest.mark.asyncio
async def test_admitted_pivot_provenance_has_one_retained_owner_and_resolves_by_reference() -> None:
    locator = "https://source.example.test/public-profile"

    async def runner(*, kind, value, purpose, consent_acknowledged):
        if kind is ResearchKind.USERNAME:
            return QuickResearchReport(
                kind=kind,
                normalized_value=value,
                observations=(
                    QuickObservation(
                        source="synthetic_public_source",
                        source_locator=locator,
                        summary="Synthetic public evidence.",
                        details={"public_email": "pivot@example.test"},
                    ),
                ),
            )
        return QuickResearchReport(kind=kind, normalized_value=value, observations=())

    report = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="seed",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )
    payload = build_converged_payload(report)
    serialized = json.dumps(payload, sort_keys=True)

    assert serialized.count(locator) == 1
    edge = payload["edges"][0]
    assert "source" not in edge
    assert "source_locator" not in edge
    decision = resolve_edge_decision(payload, edge)
    assert decision["decision"] == "admitted"
    assert decision["source_observation_index"] == 0
    assert "source" not in decision
    assert "source_locator" not in decision

    hydrated = hydrate_case_report_edge_provenance({"converged_report": payload})
    hydrated_edge = hydrated["converged_report"]["edges"][0]
    assert hydrated_edge["source"] == "synthetic_public_source"
    assert hydrated_edge["source_locator"] == locator
    assert json.dumps(payload, sort_keys=True).count(locator) == 1


@pytest.mark.asyncio
async def test_duplicate_and_nonexecuted_lead_origins_keep_distinct_observation_references() -> None:
    async def runner(*, kind, value, purpose, consent_acknowledged):
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
        return QuickResearchReport(kind=kind, normalized_value=value, observations=())

    report = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="seed",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )
    payload = build_converged_payload(report)
    decisions = [
        item
        for item in payload["lead_graph"]["decisions"]
        if item["lead_key"] == "email:same@example.test"
    ]

    assert len(decisions) == 2
    assert {item["decision"] for item in decisions} == {"admitted", "duplicate"}
    assert {item["source_observation_index"] for item in decisions} == {0, 1}


@pytest.mark.asyncio
async def test_new_edge_reference_reader_fails_closed_on_malformed_reference() -> None:
    async def runner(*, kind, value, purpose, consent_acknowledged):
        if kind is ResearchKind.USERNAME:
            return QuickResearchReport(
                kind=kind,
                normalized_value=value,
                observations=(
                    QuickObservation(
                        source="source_one",
                        source_locator="https://one.example.test",
                        summary="one",
                        details={"public_email": "pivot@example.test"},
                    ),
                ),
            )
        return QuickResearchReport(kind=kind, normalized_value=value, observations=())

    report = await run_converged_research(
        kind=ResearchKind.USERNAME,
        value="seed",
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=True,
        runner=runner,
    )
    payload = build_converged_payload(report)

    malformed = deepcopy(payload)
    malformed["edges"][0]["lead_decision_index"] = 999
    with pytest.raises(ConvergedReportReferenceError, match="out of range"):
        hydrate_case_report_edge_provenance({"converged_report": malformed})

    malformed = deepcopy(payload)
    malformed["lead_graph"]["decisions"][0]["source_observation_index"] = 999
    with pytest.raises(ConvergedReportReferenceError, match="out of range"):
        hydrate_case_report_edge_provenance({"converged_report": malformed})


def test_legacy_retained_edge_provenance_remains_readable() -> None:
    legacy = {
        "converged_report": {
            "edges": [
                {
                    "parent_key": "username:seed",
                    "child_key": "email:pivot@example.test",
                    "reason": "public_email",
                    "source": "legacy_source",
                    "source_locator": "https://legacy.example.test",
                }
            ]
        }
    }

    hydrated = hydrate_case_report_edge_provenance(legacy)
    assert hydrated == legacy
