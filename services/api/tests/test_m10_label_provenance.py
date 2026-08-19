# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib

import pytest

from app.intelligence.frontier import compatibility_frontier_limits
from app.intelligence.graph_limit_evaluation import GraphLimitScenario
from app.intelligence.m10_fixture_library import broadened_synthetic_m10_cohort
from app.intelligence.m10_label_provenance import (
    M10FixtureLabelProvenance,
    M10LabelBasis,
    build_m10_label_manifest,
)
from app.intelligence.m10_replay import build_m10_replay_record


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


def _synthetic_provenance(fixtures):
    return tuple(
        M10FixtureLabelProvenance(
            fixture_name=fixture.name,
            basis=M10LabelBasis.SYNTHETIC,
            evidence_digest=_digest(f"synthetic-label-definition:{fixture.name}:v1"),
        )
        for fixture in fixtures
    )


def test_label_manifest_keeps_synthetic_label_corpus_separate() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    manifest = build_m10_label_manifest(
        fixtures=fixtures,
        replay=_replay(fixtures),
        provenance=_synthetic_provenance(fixtures),
    )

    assert manifest.fixture_count == 6
    assert manifest.synthetic_fixture_count == 6
    assert manifest.consented_fixture_count == 0
    assert manifest.independently_reviewed_fixture_count == 0
    assert manifest.declared_label_count == 12
    assert manifest.synthetic_declared_label_count == 12
    assert manifest.consented_declared_label_count == 0
    assert manifest.independently_reviewed_declared_label_count == 0
    assert manifest.declared_relevant_label_count == 8
    assert manifest.declared_wrong_label_count == 4


def test_label_manifest_tracks_consented_labels_without_raw_evidence() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    provenance = list(_synthetic_provenance(fixtures))
    first = fixtures[0]
    provenance[0] = M10FixtureLabelProvenance(
        fixture_name=first.name,
        basis=M10LabelBasis.CONSENTED,
        evidence_digest=_digest("opaque-consent-record-001"),
    )

    manifest = build_m10_label_manifest(
        fixtures=fixtures,
        replay=_replay(fixtures),
        provenance=provenance,
    )

    assert manifest.consented_fixture_count == 1
    assert manifest.consented_declared_label_count == len(first.pivot_relevance_by_key)
    assert manifest.independently_reviewed_fixture_count == 0
    assert manifest.synthetic_declared_label_count == (
        manifest.declared_label_count - manifest.consented_declared_label_count
    )


def test_label_manifest_tracks_independent_review_without_calling_it_consent() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    provenance = list(_synthetic_provenance(fixtures))
    first = fixtures[0]
    provenance[0] = M10FixtureLabelProvenance(
        fixture_name=first.name,
        basis=M10LabelBasis.INDEPENDENTLY_REVIEWED,
        evidence_digest=_digest("opaque-independent-review-record-001"),
    )

    manifest = build_m10_label_manifest(
        fixtures=fixtures,
        replay=_replay(fixtures),
        provenance=provenance,
    )

    declared = len(first.pivot_relevance_by_key)
    assert manifest.independently_reviewed_fixture_count == 1
    assert manifest.independently_reviewed_declared_label_count == declared
    assert manifest.consented_fixture_count == 0
    assert manifest.consented_declared_label_count == 0
    assert manifest.synthetic_declared_label_count == manifest.declared_label_count - declared


def test_label_manifest_is_order_invariant_for_independent_fixtures() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    replay = _replay(fixtures)
    forward = build_m10_label_manifest(
        fixtures=fixtures,
        replay=replay,
        provenance=_synthetic_provenance(fixtures),
    )
    reverse = build_m10_label_manifest(
        fixtures=reversed(fixtures),
        replay=replay,
        provenance=reversed(_synthetic_provenance(fixtures)),
    )

    assert reverse.manifest_digest == forward.manifest_digest
    assert reverse == forward


def test_label_manifest_rejects_fixture_replay_drift() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    replay = _replay(fixtures)

    with pytest.raises(ValueError, match="replay does not match"):
        build_m10_label_manifest(
            fixtures=fixtures[:-1],
            replay=replay,
            provenance=_synthetic_provenance(fixtures[:-1]),
        )


def test_label_manifest_requires_exact_provenance_coverage() -> None:
    fixtures = broadened_synthetic_m10_cohort()
    replay = _replay(fixtures)
    provenance = _synthetic_provenance(fixtures)

    with pytest.raises(ValueError, match="cover the fixture cohort exactly"):
        build_m10_label_manifest(
            fixtures=fixtures,
            replay=replay,
            provenance=provenance[:-1],
        )


def test_label_provenance_requires_opaque_sha256_reference() -> None:
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        M10FixtureLabelProvenance(
            fixture_name="example",
            basis=M10LabelBasis.CONSENTED,
            evidence_digest="consent@example.com",
        )
