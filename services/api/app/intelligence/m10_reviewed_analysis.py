# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from .m10_consented_analysis import M10CountFraction
from .m10_label_provenance import (
    M10LabelBasis,
    build_m10_label_manifest,
)
from .m10_replay import M10ReplayRecord

_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class M10ReviewedScenarioAccounting:
    """Scenario-specific admitted-label accounting for one reviewed cohort."""

    scenario_name: str
    declared_relevant_label_count: int
    declared_wrong_label_count: int
    admitted_label_count: int
    admitted_relevant_count: int
    admitted_wrong_count: int
    missed_relevant_count: int
    not_admitted_wrong_count: int
    admitted_wrong_fraction: M10CountFraction | None
    relevant_recall_fraction: M10CountFraction | None


@dataclass(frozen=True, slots=True)
class M10ReviewedCohortAnalysis:
    """Replay-anchored accounting for an independently reviewed cohort.

    The result is descriptive within the reviewed corpus. Independent review is
    not consent, population sampling, calibration evidence, confidence or
    identity probability.
    """

    schema_version: int
    replay_input_digest: str
    replay_result_digest: str
    label_manifest_digest: str
    analysis_digest: str
    scenarios: tuple[M10ReviewedScenarioAccounting, ...]


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_m10_reviewed_cohort_analysis(
    *,
    fixtures,
    replay: M10ReplayRecord,
    provenance,
) -> M10ReviewedCohortAnalysis:
    """Build exact scenario accounting for independently reviewed labels only.

    This boundary rejects synthetic, consented and mixed provenance. Every
    admitted pivot must have a declared label. Returned fractions remain exact
    count fractions for this reviewed corpus and must not be reported as
    population false-positive/false-negative rates.
    """

    fixture_tuple = tuple(sorted(tuple(fixtures), key=lambda item: item.name))
    provenance_tuple = tuple(provenance)
    manifest = build_m10_label_manifest(
        fixtures=fixture_tuple,
        replay=replay,
        provenance=provenance_tuple,
    )

    if manifest.synthetic_fixture_count != 0 or manifest.consented_fixture_count != 0:
        raise ValueError(
            "M10 reviewed analysis rejects synthetic, consented or mixed label provenance."
        )
    if manifest.independently_reviewed_fixture_count != manifest.fixture_count:
        raise ValueError("M10 reviewed analysis requires every fixture to be independently reviewed.")
    if (
        manifest.independently_reviewed_declared_label_count
        != manifest.declared_label_count
    ):
        raise ValueError("M10 reviewed analysis requires every declared label to be independently reviewed.")
    if any(
        item.basis is not M10LabelBasis.INDEPENDENTLY_REVIEWED
        for item in provenance_tuple
    ):
        raise ValueError("M10 reviewed analysis requires independently reviewed provenance only.")

    scenario_results = (replay.comparison.baseline, *replay.comparison.candidates)
    scenario_names = [item.scenario.name for item in scenario_results]
    if len(set(scenario_names)) != len(scenario_names):
        raise ValueError("M10 reviewed analysis requires unique scenario names.")

    scenario_accounting: list[M10ReviewedScenarioAccounting] = []
    for result in scenario_results:
        counters = result.counters
        if counters.unlabelled_admitted_pivot_count != 0:
            raise ValueError(
                "M10 reviewed analysis requires complete labels for every admitted pivot."
            )
        if counters.labelled_admitted_pivot_count != (
            counters.relevant_pivot_count + counters.wrong_pivot_count
        ):
            raise ValueError("M10 admitted label counters are internally inconsistent.")

        missed_relevant = (
            manifest.declared_relevant_label_count - counters.relevant_pivot_count
        )
        not_admitted_wrong = manifest.declared_wrong_label_count - counters.wrong_pivot_count
        if missed_relevant < 0 or not_admitted_wrong < 0:
            raise ValueError(
                "M10 scenario admits more labelled pivots than the reviewed corpus declares."
            )

        admitted_wrong_fraction = None
        if counters.labelled_admitted_pivot_count:
            admitted_wrong_fraction = M10CountFraction(
                numerator=counters.wrong_pivot_count,
                denominator=counters.labelled_admitted_pivot_count,
            )

        relevant_recall_fraction = None
        if manifest.declared_relevant_label_count:
            relevant_recall_fraction = M10CountFraction(
                numerator=counters.relevant_pivot_count,
                denominator=manifest.declared_relevant_label_count,
            )

        scenario_accounting.append(
            M10ReviewedScenarioAccounting(
                scenario_name=result.scenario.name,
                declared_relevant_label_count=manifest.declared_relevant_label_count,
                declared_wrong_label_count=manifest.declared_wrong_label_count,
                admitted_label_count=counters.labelled_admitted_pivot_count,
                admitted_relevant_count=counters.relevant_pivot_count,
                admitted_wrong_count=counters.wrong_pivot_count,
                missed_relevant_count=missed_relevant,
                not_admitted_wrong_count=not_admitted_wrong,
                admitted_wrong_fraction=admitted_wrong_fraction,
                relevant_recall_fraction=relevant_recall_fraction,
            )
        )

    canonical_scenarios = tuple(sorted(scenario_accounting, key=lambda item: item.scenario_name))
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "replay_input_digest": replay.input_digest,
        "replay_result_digest": replay.result_digest,
        "label_manifest_digest": manifest.manifest_digest,
        "scenarios": [asdict(item) for item in canonical_scenarios],
    }
    return M10ReviewedCohortAnalysis(
        schema_version=_SCHEMA_VERSION,
        replay_input_digest=replay.input_digest,
        replay_result_digest=replay.result_digest,
        label_manifest_digest=manifest.manifest_digest,
        analysis_digest=_sha256_json(payload),
        scenarios=canonical_scenarios,
    )
