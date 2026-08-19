# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_limit_evaluation import GraphLimitScenario
from app.intelligence.m10_consented_analysis import M10CountFraction
from app.intelligence.m10_fixture_library import broadened_synthetic_m10_cohort
from app.intelligence.m10_label_provenance import (
    M10FixtureLabelProvenance,
    M10LabelBasis,
)
from app.intelligence.m10_replay import build_m10_replay_record
from app.intelligence.m10_reviewed_analysis import build_m10_reviewed_cohort_analysis


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _replay(fixtures):
    return build_m10_replay_record(
        fixtures=fixtures,
        baseline=GraphLimitScenario(
            name="production_depth_2_nodes_12",
            limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
        ),
        candidates=(
            GraphLimitScenario(
                name="candidate_depth_3_nodes_12",
                limits=compatibility_frontier_limits(max_depth=3, max_nodes=12),
            ),
        ),
    )


def _provenance(fixtures, *, basis: M10LabelBasis):
    return tuple(
        M10FixtureLabelProvenance(
            fixture_name=fixture.name,
            basis=basis,
            evidence_digest=_digest(f"review-contract-record:{fixture.name}:v1"),
        )
        for fixture in fixtures
    )


def _by_name(analysis):
    return {item.scenario_name: item for item in analysis.scenarios}


def test_reviewed_analysis_uses_exact_scenario_denominators() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    analysis = build_m10_reviewed_cohort_analysis(
        fixtures=fixtures,
        replay=_replay(fixtures),
        provenance=_provenance(fixtures, basis=M10LabelBasis.INDEPENDENTLY_REVIEWED),
    )
    scenarios = _by_name(analysis)

    baseline = scenarios["production_depth_2_nodes_12"]
    assert baseline.declared_relevant_label_count == 8
    assert baseline.declared_wrong_label_count == 4
    assert baseline.admitted_label_count == 9
    assert baseline.admitted_relevant_count == 8
    assert baseline.admitted_wrong_count == 1
    assert baseline.missed_relevant_count == 0
    assert baseline.not_admitted_wrong_count == 3
    assert baseline.admitted_wrong_fraction == M10CountFraction(1, 9)
    assert baseline.relevant_recall_fraction == M10CountFraction(8, 8)

    deeper = scenarios["candidate_depth_3_nodes_12"]
    assert deeper.admitted_label_count == 12
    assert deeper.admitted_relevant_count == 8
    assert deeper.admitted_wrong_count == 4
    assert deeper.missed_relevant_count == 0
    assert deeper.not_admitted_wrong_count == 0
    assert deeper.admitted_wrong_fraction == M10CountFraction(4, 12)
    assert deeper.relevant_recall_fraction == M10CountFraction(8, 8)


def test_reviewed_analysis_rejects_consent_synthetic_and_mixed_provenance() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    replay = _replay(fixtures)

    for basis in (M10LabelBasis.SYNTHETIC, M10LabelBasis.CONSENTED):
        with pytest.raises(ValueError, match="rejects synthetic, consented or mixed"):
            build_m10_reviewed_cohort_analysis(
                fixtures=fixtures,
                replay=replay,
                provenance=_provenance(fixtures, basis=basis),
            )

    mixed = list(
        _provenance(fixtures, basis=M10LabelBasis.INDEPENDENTLY_REVIEWED)
    )
    mixed[0] = replace(mixed[0], basis=M10LabelBasis.CONSENTED)
    with pytest.raises(ValueError, match="rejects synthetic, consented or mixed"):
        build_m10_reviewed_cohort_analysis(
            fixtures=fixtures,
            replay=replay,
            provenance=mixed,
        )


def test_reviewed_analysis_rejects_unlabelled_admitted_pivots() -> None:
    fixtures = tuple(
        replace(fixture, pivot_relevance_by_key={})
        for fixture in broadened_synthetic_m10_cohort()
    )

    with pytest.raises(ValueError, match="complete labels for every admitted pivot"):
        build_m10_reviewed_cohort_analysis(
            fixtures=fixtures,
            replay=_replay(fixtures),
            provenance=_provenance(
                fixtures,
                basis=M10LabelBasis.INDEPENDENTLY_REVIEWED,
            ),
        )


def test_reviewed_analysis_is_replay_and_manifest_anchored() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    replay = _replay(fixtures)
    provenance = _provenance(
        fixtures,
        basis=M10LabelBasis.INDEPENDENTLY_REVIEWED,
    )

    forward = build_m10_reviewed_cohort_analysis(
        fixtures=fixtures,
        replay=replay,
        provenance=provenance,
    )
    reverse = build_m10_reviewed_cohort_analysis(
        fixtures=reversed(fixtures),
        replay=replay,
        provenance=reversed(provenance),
    )

    assert reverse.analysis_digest == forward.analysis_digest
    assert reverse.label_manifest_digest == forward.label_manifest_digest
    assert reverse == forward
