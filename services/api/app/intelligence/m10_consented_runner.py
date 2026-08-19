# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
    canonicalize_lead,
)
from .frontier import compatibility_frontier_limits
from .graph_evaluation import PivotRelevance
from .graph_limit_evaluation import GraphFixtureLead, GraphLimitScenario
from .m10_cohort import M10GraphFixture
from .m10_consented_analysis import (
    M10ConsentedCohortAnalysis,
    build_m10_consented_cohort_analysis,
)
from .m10_label_provenance import M10FixtureLabelProvenance, M10LabelBasis
from .m10_replay import build_m10_replay_record

_SCHEMA_VERSION = 1
_MAX_FILE_BYTES = 1_048_576
_MAX_FIXTURES = 256
_MAX_NODES = 2_048
_MAX_TEXT = 4_096
_SHA256_HEX_LENGTH = 64


@dataclass(frozen=True, slots=True)
class M10LocalConsentedRun:
    """Privacy-bounded result of one local consented-cohort evaluation."""

    schema_version: int
    cohort_name_digest: str
    local_input_digest: str
    replay_input_digest: str
    replay_result_digest: str
    label_manifest_digest: str
    analysis_digest: str
    fixture_count: int
    scenarios: tuple[dict[str, object], ...]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _text(value: object, *, field: str, max_length: int = _MAX_TEXT) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string.")
    if not value or value.strip() != value:
        raise ValueError(f"{field} must be non-empty and trimmed.")
    if len(value) > max_length:
        raise ValueError(f"{field} exceeds the {max_length}-character limit.")
    return value


def _enum(enum_type, value: object, *, field: str):
    text = _text(value, field=field, max_length=128)
    try:
        return enum_type(text)
    except ValueError as exc:
        raise ValueError(f"{field} has an unsupported value.") from exc


def _object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    return value


def _list(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list.")
    return value


def _canonical_key(kind: LeadKind, value: str) -> tuple[str, str]:
    normalized, comparison_key = canonicalize_lead(kind, value)
    return normalized, f"{kind.value}:{comparison_key}"


def _build_fixture(raw: dict[str, Any]) -> tuple[M10GraphFixture, M10FixtureLabelProvenance, int]:
    name = _text(raw.get("name"), field="fixture.name", max_length=128)
    evidence_digest = _text(
        raw.get("evidence_digest"), field=f"fixture[{name}].evidence_digest", max_length=64
    )
    if len(evidence_digest) != _SHA256_HEX_LENGTH or any(
        char not in "0123456789abcdef" for char in evidence_digest
    ):
        raise ValueError(f"fixture[{name}].evidence_digest must be lowercase SHA-256.")

    seed = _object(raw.get("seed"), field=f"fixture[{name}].seed")
    seed_id = _text(seed.get("id"), field=f"fixture[{name}].seed.id", max_length=128)
    seed_kind = _enum(LeadKind, seed.get("kind"), field=f"fixture[{name}].seed.kind")
    seed_value = _text(seed.get("value"), field=f"fixture[{name}].seed.value")
    _, seed_key = _canonical_key(seed_kind, seed_value)

    node_key_by_id: dict[str, str] = {seed_id: seed_key}
    parentable_ids = {seed_id}
    leads_by_parent: dict[str, list[GraphFixtureLead]] = {}
    relevance_by_key: dict[str, PivotRelevance] = {}

    nodes = _list(raw.get("nodes", []), field=f"fixture[{name}].nodes")
    for index, item in enumerate(nodes):
        node = _object(item, field=f"fixture[{name}].nodes[{index}]")
        node_id = _text(
            node.get("id"), field=f"fixture[{name}].nodes[{index}].id", max_length=128
        )
        if node_id in node_key_by_id:
            raise ValueError(f"fixture[{name}] contains a duplicate node id.")
        parent_id = _text(
            node.get("parent_id"),
            field=f"fixture[{name}].nodes[{index}].parent_id",
            max_length=128,
        )
        if parent_id not in parentable_ids:
            raise ValueError(
                f"fixture[{name}] node must reference the seed or an earlier successful "
                "automatic node as parent."
            )

        kind = _enum(LeadKind, node.get("kind"), field=f"fixture[{name}].nodes[{index}].kind")
        value = _text(node.get("value"), field=f"fixture[{name}].nodes[{index}].value")
        normalized_value, candidate_key = _canonical_key(kind, value)
        reason = _enum(
            LeadReason, node.get("reason"), field=f"fixture[{name}].nodes[{index}].reason"
        )
        disposition = _enum(
            LeadDisposition,
            node.get("disposition"),
            field=f"fixture[{name}].nodes[{index}].disposition",
        )
        source = _text(node.get("source"), field=f"fixture[{name}].nodes[{index}].source")
        source_locator = _text(
            node.get("source_locator"),
            field=f"fixture[{name}].nodes[{index}].source_locator",
        )
        field_name = _text(
            node.get("field_name"), field=f"fixture[{name}].nodes[{index}].field_name"
        )
        provider_fails = node.get("provider_fails", False)
        if not isinstance(provider_fails, bool):
            raise ValueError(f"fixture[{name}] provider_fails must be boolean.")

        actual_key = None
        actual_value = node.get("actual_value")
        if actual_value is not None:
            if provider_fails:
                raise ValueError(f"fixture[{name}] cannot fail and return actual_value.")
            actual_text = _text(
                actual_value, field=f"fixture[{name}].nodes[{index}].actual_value"
            )
            _, actual_key = _canonical_key(kind, actual_text)

        candidate = LeadCandidate(
            kind=kind,
            value=normalized_value,
            comparison_key=candidate_key.split(":", 1)[1],
            reason=reason,
            disposition=disposition,
            source=source,
            source_locator=source_locator,
            field_name=field_name,
        )
        fixture_lead = GraphFixtureLead(
            candidate=candidate,
            provider_fails=provider_fails,
            actual_key=actual_key,
        )
        result_key = fixture_lead.result_key
        node_key_by_id[node_id] = result_key
        parent_key = node_key_by_id[parent_id]
        leads_by_parent.setdefault(parent_key, []).append(fixture_lead)

        can_parent = disposition is LeadDisposition.AUTO_PIVOT and not provider_fails
        if can_parent:
            parentable_ids.add(node_id)

        relevance = node.get("relevance")
        if relevance is not None:
            if not can_parent:
                raise ValueError(
                    f"fixture[{name}] can only label a successful automatic pivot."
                )
            label = _enum(
                PivotRelevance,
                relevance,
                field=f"fixture[{name}].nodes[{index}].relevance",
            )
            existing = relevance_by_key.get(result_key)
            if existing is not None and existing is not label:
                raise ValueError(f"fixture[{name}] assigns conflicting labels to one result.")
            relevance_by_key[result_key] = label

    fixture = M10GraphFixture(
        name=name,
        seed_key=seed_key,
        seed_kind=seed_kind,
        leads_by_parent={key: tuple(value) for key, value in leads_by_parent.items()},
        pivot_relevance_by_key=relevance_by_key,
    )
    provenance = M10FixtureLabelProvenance(
        fixture_name=name,
        basis=M10LabelBasis.CONSENTED,
        evidence_digest=evidence_digest,
    )
    return fixture, provenance, len(nodes)


def _scenario_accounting_payload(
    analysis: M10ConsentedCohortAnalysis,
) -> tuple[dict[str, object], ...]:
    return tuple(asdict(scenario) for scenario in analysis.scenarios)


def evaluate_local_consented_payload(payload: object, *, input_digest: str) -> M10LocalConsentedRun:
    """Validate and evaluate one private local cohort without retaining its identifiers."""

    root = _object(payload, field="cohort")
    if root.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError(f"cohort.schema_version must equal {_SCHEMA_VERSION}.")
    cohort_name = _text(root.get("cohort_name"), field="cohort.cohort_name", max_length=128)
    raw_fixtures = _list(root.get("fixtures"), field="cohort.fixtures")
    if not raw_fixtures:
        raise ValueError("cohort.fixtures must contain at least one fixture.")
    if len(raw_fixtures) > _MAX_FIXTURES:
        raise ValueError(f"cohort.fixtures exceeds the {_MAX_FIXTURES}-fixture limit.")

    fixtures: list[M10GraphFixture] = []
    provenance: list[M10FixtureLabelProvenance] = []
    total_nodes = 0
    fixture_names: set[str] = set()
    for raw in raw_fixtures:
        fixture, item_provenance, node_count = _build_fixture(_object(raw, field="fixture"))
        if fixture.name in fixture_names:
            raise ValueError("cohort contains a duplicate fixture name.")
        fixture_names.add(fixture.name)
        total_nodes += node_count
        if total_nodes > _MAX_NODES:
            raise ValueError(f"cohort exceeds the {_MAX_NODES}-node limit.")
        fixtures.append(fixture)
        provenance.append(item_provenance)

    baseline = GraphLimitScenario(
        name="production_depth_2_nodes_12",
        limits=compatibility_frontier_limits(max_depth=2, max_nodes=12),
    )
    candidate = GraphLimitScenario(
        name="candidate_depth_3_nodes_12",
        limits=compatibility_frontier_limits(max_depth=3, max_nodes=12),
    )
    replay = build_m10_replay_record(
        fixtures=tuple(fixtures),
        baseline=baseline,
        candidates=(candidate,),
    )
    analysis = build_m10_consented_cohort_analysis(
        fixtures=tuple(fixtures),
        replay=replay,
        provenance=tuple(provenance),
    )
    return M10LocalConsentedRun(
        schema_version=_SCHEMA_VERSION,
        cohort_name_digest=_sha256_text(cohort_name),
        local_input_digest=input_digest,
        replay_input_digest=replay.input_digest,
        replay_result_digest=replay.result_digest,
        label_manifest_digest=analysis.label_manifest_digest,
        analysis_digest=analysis.analysis_digest,
        fixture_count=len(fixtures),
        scenarios=_scenario_accounting_payload(analysis),
    )


def evaluate_local_consented_file(path: Path) -> M10LocalConsentedRun:
    """Load a bounded local JSON cohort and return aggregate/digest output only."""

    raw = path.read_bytes()
    if len(raw) > _MAX_FILE_BYTES:
        raise ValueError(f"M10 consented cohort file exceeds {_MAX_FILE_BYTES} bytes.")
    input_digest = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("M10 consented cohort file must be valid UTF-8 JSON.") from exc
    return evaluate_local_consented_payload(payload, input_digest=input_digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a private consented M10 cohort locally. Output contains only "
            "aggregate counts and replay/provenance digests; the input file is not retained."
        )
    )
    parser.add_argument("cohort", type=Path, help="Path to a local consented-cohort JSON file")
    args = parser.parse_args(argv)
    try:
        result = evaluate_local_consented_file(args.cohort)
    except (OSError, ValueError):
        print("M10 consented cohort validation failed.", file=sys.stderr)
        return 2
    print(json.dumps(asdict(result), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main() tests
    raise SystemExit(main())
