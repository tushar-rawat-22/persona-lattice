# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadKind,
    LeadReason,
    canonicalize_lead,
)
from .graph_evaluation import PivotRelevance
from .graph_limit_evaluation import GraphFixtureLead
from .m10_cohort import M10GraphFixture
from .m10_label_provenance import M10FixtureLabelProvenance, M10LabelBasis

LOCAL_COHORT_SCHEMA_VERSION = 1
MAX_LOCAL_COHORT_FILE_BYTES = 1_048_576
MAX_LOCAL_COHORT_FIXTURES = 256
MAX_LOCAL_COHORT_NODES = 2_048
_MAX_TEXT = 4_096
_SHA256_HEX_LENGTH = 64


@dataclass(frozen=True, slots=True)
class M10MaterializedLocalCohort:
    """Validated private local fixture material before replay/evaluation."""

    cohort_name: str
    fixtures: tuple[M10GraphFixture, ...]
    provenance: tuple[M10FixtureLabelProvenance, ...]


def sha256_text(value: str) -> str:
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


def _build_fixture(
    raw: dict[str, Any],
    *,
    basis: M10LabelBasis,
) -> tuple[M10GraphFixture, M10FixtureLabelProvenance, int]:
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
        basis=basis,
        evidence_digest=evidence_digest,
    )
    return fixture, provenance, len(nodes)


def materialize_local_labelled_payload(
    payload: object,
    *,
    basis: M10LabelBasis,
) -> M10MaterializedLocalCohort:
    """Validate one local labelled cohort and bind it to one fixed provenance basis.

    Callers choose the basis in code, not from the input file. This prevents a
    private JSON file from upgrading its own evidence basis.
    """

    if basis is M10LabelBasis.SYNTHETIC:
        raise ValueError("Local evidence-backed cohorts cannot use synthetic provenance.")

    root = _object(payload, field="cohort")
    if root.get("schema_version") != LOCAL_COHORT_SCHEMA_VERSION:
        raise ValueError(f"cohort.schema_version must equal {LOCAL_COHORT_SCHEMA_VERSION}.")
    cohort_name = _text(root.get("cohort_name"), field="cohort.cohort_name", max_length=128)
    raw_fixtures = _list(root.get("fixtures"), field="cohort.fixtures")
    if not raw_fixtures:
        raise ValueError("cohort.fixtures must contain at least one fixture.")
    if len(raw_fixtures) > MAX_LOCAL_COHORT_FIXTURES:
        raise ValueError(
            f"cohort.fixtures exceeds the {MAX_LOCAL_COHORT_FIXTURES}-fixture limit."
        )

    fixtures: list[M10GraphFixture] = []
    provenance: list[M10FixtureLabelProvenance] = []
    total_nodes = 0
    fixture_names: set[str] = set()
    for raw in raw_fixtures:
        fixture, item_provenance, node_count = _build_fixture(
            _object(raw, field="fixture"),
            basis=basis,
        )
        if fixture.name in fixture_names:
            raise ValueError("cohort contains a duplicate fixture name.")
        fixture_names.add(fixture.name)
        total_nodes += node_count
        if total_nodes > MAX_LOCAL_COHORT_NODES:
            raise ValueError(f"cohort exceeds the {MAX_LOCAL_COHORT_NODES}-node limit.")
        fixtures.append(fixture)
        provenance.append(item_provenance)

    return M10MaterializedLocalCohort(
        cohort_name=cohort_name,
        fixtures=tuple(fixtures),
        provenance=tuple(provenance),
    )


def load_local_labelled_file(path: Path, *, label: str) -> tuple[object, str]:
    """Read one bounded private JSON file and return parsed data plus byte digest."""

    raw = path.read_bytes()
    if len(raw) > MAX_LOCAL_COHORT_FILE_BYTES:
        raise ValueError(f"M10 {label} cohort file exceeds {MAX_LOCAL_COHORT_FILE_BYTES} bytes.")
    input_digest = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"M10 {label} cohort file must be valid UTF-8 JSON.") from exc
    return payload, input_digest
