# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum

from .graph_evaluation import PivotRelevance
from .m10_cohort import M10GraphFixture
from .m10_replay import M10ReplayRecord, build_m10_replay_record

_SCHEMA_VERSION = 1
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class M10LabelBasis(StrEnum):
    """Allowed ground-truth provenance classes for labelled M10 fixtures."""

    SYNTHETIC = "synthetic"
    CONSENTED = "consented"


@dataclass(frozen=True, slots=True)
class M10FixtureLabelProvenance:
    """Privacy-bounded provenance for one fixture's relevance labels.

    `evidence_digest` is an opaque SHA-256 reference to the external label/consent
    evidence. Raw consent text, personal identifiers and source documents do not
    belong in the M10 experiment manifest.
    """

    fixture_name: str
    basis: M10LabelBasis
    evidence_digest: str

    def __post_init__(self) -> None:
        if not self.fixture_name or self.fixture_name.strip() != self.fixture_name:
            raise ValueError("M10 label provenance fixture_name must be non-empty and trimmed.")
        if not _SHA256_RE.fullmatch(self.evidence_digest):
            raise ValueError("M10 label provenance evidence_digest must be lowercase SHA-256.")


@dataclass(frozen=True, slots=True)
class M10LabelManifest:
    """Replay-anchored label provenance and count-only denominator metadata."""

    schema_version: int
    replay_input_digest: str
    replay_result_digest: str
    manifest_digest: str
    fixture_count: int
    synthetic_fixture_count: int
    consented_fixture_count: int
    labelled_pivot_count: int
    synthetic_labelled_pivot_count: int
    consented_labelled_pivot_count: int
    relevant_pivot_count: int
    wrong_pivot_count: int


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_m10_label_manifest(
    *,
    fixtures,
    replay: M10ReplayRecord,
    provenance,
) -> M10LabelManifest:
    """Bind fixture labels to explicit provenance and the exact M10 replay.

    The builder intentionally returns counts, not error rates. A synthetic label
    can support deterministic regression tests but must remain distinguishable
    from consented ground truth before any future false-positive/false-negative
    analysis is attempted.
    """

    fixture_tuple = tuple(sorted(tuple(fixtures), key=lambda item: item.name))
    if not fixture_tuple:
        raise ValueError("M10 label manifest requires at least one fixture.")

    rebuilt = build_m10_replay_record(
        fixtures=fixture_tuple,
        baseline=replay.comparison.baseline.scenario,
        candidates=tuple(result.scenario for result in replay.comparison.candidates),
    )
    if (
        rebuilt.input_digest != replay.input_digest
        or rebuilt.result_digest != replay.result_digest
    ):
        raise ValueError("M10 label manifest replay does not match the supplied fixtures.")

    provenance_tuple = tuple(provenance)
    names = [item.fixture_name for item in provenance_tuple]
    if len(set(names)) != len(names):
        raise ValueError("M10 label provenance contains duplicate fixture names.")

    fixture_names = {fixture.name for fixture in fixture_tuple}
    provenance_names = set(names)
    if provenance_names != fixture_names:
        missing = sorted(fixture_names - provenance_names)
        extra = sorted(provenance_names - fixture_names)
        raise ValueError(
            "M10 label provenance must cover the fixture cohort exactly: "
            f"missing={missing!r}, extra={extra!r}."
        )

    provenance_by_name = {item.fixture_name: item for item in provenance_tuple}
    labelled = relevant = wrong = 0
    synthetic_labelled = consented_labelled = 0
    synthetic_fixtures = consented_fixtures = 0

    manifest_fixtures: list[dict[str, object]] = []
    for fixture in fixture_tuple:
        item = provenance_by_name[fixture.name]
        pivot_labels = [
            [key, fixture.pivot_relevance_by_key[key].value]
            for key in sorted(fixture.pivot_relevance_by_key)
        ]
        labelled_count = len(pivot_labels)
        relevant_count = sum(
            1
            for value in fixture.pivot_relevance_by_key.values()
            if value is PivotRelevance.RELEVANT
        )
        wrong_count = sum(
            1
            for value in fixture.pivot_relevance_by_key.values()
            if value is PivotRelevance.WRONG
        )
        if relevant_count + wrong_count != labelled_count:
            raise ValueError("M10 fixture contains an unsupported pivot relevance label.")

        labelled += labelled_count
        relevant += relevant_count
        wrong += wrong_count
        if item.basis is M10LabelBasis.SYNTHETIC:
            synthetic_fixtures += 1
            synthetic_labelled += labelled_count
        elif item.basis is M10LabelBasis.CONSENTED:
            consented_fixtures += 1
            consented_labelled += labelled_count
        else:  # defensive against forged enum-like values
            raise ValueError("M10 label provenance uses an unsupported basis.")

        manifest_fixtures.append(
            {
                "fixture_name": fixture.name,
                "basis": item.basis.value,
                "evidence_digest": item.evidence_digest,
                "pivot_labels": pivot_labels,
            }
        )

    payload = {
        "schema_version": _SCHEMA_VERSION,
        "replay_input_digest": replay.input_digest,
        "replay_result_digest": replay.result_digest,
        "fixtures": manifest_fixtures,
    }
    return M10LabelManifest(
        schema_version=_SCHEMA_VERSION,
        replay_input_digest=replay.input_digest,
        replay_result_digest=replay.result_digest,
        manifest_digest=_sha256_json(payload),
        fixture_count=len(fixture_tuple),
        synthetic_fixture_count=synthetic_fixtures,
        consented_fixture_count=consented_fixtures,
        labelled_pivot_count=labelled,
        synthetic_labelled_pivot_count=synthetic_labelled,
        consented_labelled_pivot_count=consented_labelled,
        relevant_pivot_count=relevant,
        wrong_pivot_count=wrong,
    )
