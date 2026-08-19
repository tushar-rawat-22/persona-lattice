# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from .m10_label_provenance import (
    M10LabelBasis,
    build_m10_label_manifest,
)
from .m10_replay import M10ReplayRecord

_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class M10CountFraction:
    """Exact count fraction; deliberately not converted to a percentage."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.denominator <= 0:
            raise ValueError("M10 count-fraction denominator must be positive.")
        if self.numerator < 0 or self.numerator > self.denominator:
            raise ValueError("M10 count-fraction numerator must be within the denominator.")


@dataclass(frozen=True, slots=True)
class M10ConsentedScenarioAccounting:
    """Scenario-specific admitted-label accounting for one consented cohort."""

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
class M10ConsentedCohortAnalysis:
    """Replay- and provenance-anchored accounting for an entirely consented cohort."""

    schema_version: int
    replay_input_digest: str
    replay_result_digest: str
    label_manifest_digest: str
    analysis_digest: str
    scenarios: tuple[M10ConsentedScenarioAccounting, ...]


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_m10_consented_cohort_analysis(
    *,
    fixtures,
    replay: M10ReplayRecord,
    provenance,
) -> M10ConsentedCohortAnalysis:
    """Build exact scenario accounting only when the whole label cohort is consented.

    This boundary intentionally refuses synthetic or mixed cohorts and any scenario
    with admitted pivots that lack labels. The returned fractions are descriptive
    within the declared consented fixture corpus; they are not population error
    rates, calibration evidence, confidence, or identity probability.
    """

    fixture_tuple = tuple(sorted(tuple(fixtures), key=lambda item: item.name))
    provenance_tuple = tuple(provenance)
    manifest = build_m10_label_manifest(
        fixtures=fixture_tuple,
        replay=replay,
        provenance=provenance_tuple,
    )

    if manifest.synthetic_fixture_count != 0:
        raise ValueError("M10 consented analysis rejects synthetic or mixed label provenance.")
    if manifest.consented_fixture_count != manifest.fixture_count:
        raise ValueError("M10 consented analysis requires every fixture to be consented.")
    if manifest.consented_declared_label_count != manifest.declared_label_count:
        raise ValueError("M10 consented analysis requires every declared label to be consented.")
    if any(item.basis is not M10LabelBasis.CONSENTED for item in provenance_tuple):
        raise ValueError("M10 consented analysis requires consented provenance only.")

    scenario_results = (replay.comparison.baseline, *replay.comparison.candidates)
    scenario_names = [item.scenario.name for item in scenario_results]
    if len(set(scenario_names)) != len(scenario_names):
        raise ValueError("M10 consented analysis requires unique scenario names.")

    scenario_accounting: list[M10ConsentedScenarioAccounting] = []
    for result in scenario_results:
        counters = result.counters
        if counters.unlabelled_admitted_pivot_count != 0:
            raise ValueError(
                "M10 consented analysis requires complete labels for every admitted pivot."
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
                "M10 scenario admits more labelled pivots than the consented corpus declares."
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
            M10ConsentedScenarioAccounting(
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
    return M10ConsentedCohortAnalysis(
        schema_version=_SCHEMA_VERSION,
        replay_input_digest=replay.input_digest,
        replay_result_digest=replay.result_digest,
        label_manifest_digest=manifest.manifest_digest,
        analysis_digest=_sha256_json(payload),
        scenarios=canonical_scenarios,
    )
