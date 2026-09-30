# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .cases import StoredCase
from .converged_report import (
    ConvergedReportReferenceError,
    validate_converged_provenance_references,
)
from .correlation import FactorKind, FactorStatus
from .intelligence.source_states import SourceRunReason, SourceRunState


class RelationshipClarityProjectionError(ValueError):
    """Raised when retained evidence cannot support a truthful projection."""


class RelationshipState(StrEnum):
    CORROBORATED = "corroborated"
    UNRESOLVED = "unresolved"
    CONTRADICTION = "contradiction"


class RelationshipNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["identifier", "observation"]
    label: str
    research_node_key: str
    depth: int
    canonical_identifier: str | None = None
    identifier_kind: str | None = None
    observation_ref: str | None = None
    source: str | None = None
    source_locator: str | None = None
    source_state: SourceRunState | None = None


class RelationshipProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_ref: str
    source: str
    source_locator: str
    source_state: SourceRunState
    summary: str
    observed_at: str | None = None
    context: dict[str, str | int | bool | None]


class RelationshipEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["evidence_factor"] = "evidence_factor"
    source_node_id: str
    target_node_id: str
    state: RelationshipState
    relationship_reason: str
    factor_kind: FactorKind
    factor_status: FactorStatus
    supporting_observation_refs: list[str]
    contradictory_observation_refs: list[str]
    identifier_refs: list[str]
    provenance: list[RelationshipProvenance]
    context: dict[str, str | int | bool | None]


class RelationshipClarityProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["relationship-clarity-projection-v1"]
    case_id: UUID
    case_created_at: str
    generated_from_report_version: str
    deterministic: Literal[True]
    probabilistic: Literal[False]
    relationship_states: tuple[
        Literal["corroborated"],
        Literal["unresolved"],
        Literal["contradiction"],
    ]
    nodes: list[RelationshipNode]
    edges: list[RelationshipEdge]


_ACTIVE_FACTOR_STATUSES = {
    FactorStatus.APPLIED,
    FactorStatus.APPLIED_UNKNOWN_FRESHNESS,
}
_CORROBORATED_FACTOR_KINDS = {
    FactorKind.EXACT_CONFIRMED_IDENTIFIER_OVERLAP,
    FactorKind.INDEPENDENT_CROSS_LINK,
}


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RelationshipClarityProjectionError(f"{label} must be an object.")
    return value


def _sequence(value: object, *, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise RelationshipClarityProjectionError(f"{label} must be an array.")
    return value


def _string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RelationshipClarityProjectionError(f"{label} must be a non-empty string.")
    return value


def _index(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RelationshipClarityProjectionError(f"{label} must be a non-negative integer.")
    return value


def _node_id(node_key: str) -> str:
    return f"identifier:{node_key}"


def _observation_id(node_key: str, observation_index: int) -> str:
    return f"observation:{node_key}:{observation_index}"


def _observation_ref(node_key: str, observation_index: int) -> str:
    return f"{node_key}#observation:{observation_index}"


def _relationship_state(kind: FactorKind, *, veto: object) -> RelationshipState:
    if not isinstance(veto, bool):
        raise RelationshipClarityProjectionError("M5 factor veto must be boolean.")
    if kind is FactorKind.HARD_CONTRADICTION:
        if not veto:
            raise RelationshipClarityProjectionError(
                "A hard contradiction must retain its explicit veto state."
            )
        return RelationshipState.CONTRADICTION
    if veto:
        raise RelationshipClarityProjectionError(
            "Only an explicit hard contradiction may carry a veto."
        )
    if kind in _CORROBORATED_FACTOR_KINDS:
        return RelationshipState.CORROBORATED
    return RelationshipState.UNRESOLVED


def _source_run_state(
    node: Mapping[str, object],
    *,
    source: str,
    node_kind: str,
) -> SourceRunState:
    source_runs = _mapping(node.get("source_runs"), label="node source_runs")
    records = _sequence(source_runs.get("records"), label="node source_runs.records")
    matches = [
        _mapping(record, label="source-run record")
        for record in records
        if isinstance(record, Mapping)
        and record.get("source") == source
        and record.get("lead_kind") == node_kind
    ]
    if len(matches) != 1:
        raise RelationshipClarityProjectionError(
            "Canonical observation provenance requires exactly one retained source-run state."
        )
    try:
        state = SourceRunState(matches[0].get("state"))
    except (TypeError, ValueError) as exc:
        raise RelationshipClarityProjectionError(
            "Canonical observation source-run state is invalid."
        ) from exc
    if state is not SourceRunState.EXECUTED:
        raise RelationshipClarityProjectionError(
            "Only an executed source with a retained observation may support a relationship."
        )
    try:
        reason = SourceRunReason(matches[0].get("reason"))
    except (TypeError, ValueError) as exc:
        raise RelationshipClarityProjectionError(
            "Canonical observation source-run reason is invalid."
        ) from exc
    if reason is not SourceRunReason.RESULTS_RETURNED:
        raise RelationshipClarityProjectionError(
            "Executed relationship provenance must retain a results-returned reason."
        )
    if matches[0].get("execution_attempted") is not True:
        raise RelationshipClarityProjectionError(
            "Executed relationship provenance must prove source execution was attempted."
        )
    observation_count = matches[0].get("observation_count")
    if isinstance(observation_count, bool) or not isinstance(observation_count, int):
        raise RelationshipClarityProjectionError(
            "Canonical source-run observation_count is invalid."
        )
    if observation_count < 1:
        raise RelationshipClarityProjectionError(
            "Executed relationship provenance must retain an observation count."
        )
    return state


def _resolve_observation(
    nodes_by_key: Mapping[str, Mapping[str, object]],
    reference: object,
    *,
    case_created_at: str,
) -> tuple[str, RelationshipNode, RelationshipProvenance]:
    item = _mapping(reference, label="factor observation reference")
    node_key = _string(item.get("node_key"), label="factor observation node_key")
    observation_index = _index(
        item.get("observation_index"),
        label="factor observation_index",
    )
    node = nodes_by_key.get(node_key)
    if node is None:
        raise RelationshipClarityProjectionError(
            "Factor observation reference does not resolve to a retained node."
        )
    observations = _sequence(node.get("observations"), label="node observations")
    if observation_index >= len(observations):
        raise RelationshipClarityProjectionError(
            "Factor observation reference is out of range."
        )
    observation = _mapping(observations[observation_index], label="canonical observation")
    source = _string(observation.get("source"), label="canonical observation source")
    source_locator = _string(
        observation.get("source_locator"),
        label="canonical observation source_locator",
    )
    summary = _string(observation.get("summary"), label="canonical observation summary")
    node_kind = _string(node.get("kind"), label="research node kind")
    source_state = _source_run_state(node, source=source, node_kind=node_kind)
    ref = _observation_ref(node_key, observation_index)
    depth = _index(node.get("depth"), label="research node depth")
    return (
        ref,
        RelationshipNode(
            id=_observation_id(node_key, observation_index),
            kind="observation",
            label=summary,
            research_node_key=node_key,
            depth=depth,
            observation_ref=ref,
            source=source,
            source_locator=source_locator,
            source_state=source_state,
        ),
        RelationshipProvenance(
            observation_ref=ref,
            source=source,
            source_locator=source_locator,
            source_state=source_state,
            summary=summary,
            observed_at=None,
            context={"case_created_at": case_created_at},
        ),
    )


def _factor_references(factor: Mapping[str, object]) -> tuple[Sequence[object], list[str]]:
    if "observation_refs" not in factor:
        raise RelationshipClarityProjectionError(
            "Retained M5 factor is missing canonical observation_refs."
        )
    if "identifier_refs" not in factor:
        raise RelationshipClarityProjectionError(
            "Retained M5 factor is missing canonical identifier_refs."
        )
    observation_refs = _sequence(
        factor.get("observation_refs"),
        label="factor observation_refs",
    )
    identifier_values = _sequence(
        factor.get("identifier_refs"),
        label="factor identifier_refs",
    )
    identifier_refs = [
        _string(value, label="factor identifier reference") for value in identifier_values
    ]
    if not observation_refs:
        raise RelationshipClarityProjectionError(
            "Every relationship factor requires canonical observation provenance."
        )
    return observation_refs, identifier_refs


def build_relationship_clarity_projection(
    record: StoredCase,
) -> RelationshipClarityProjection:
    """Derive a bounded relationship projection from retained canonical references.

    The builder deliberately rejects legacy retained M5 factors that do not carry
    canonical references. It never hydrates missing provenance or interprets source
    execution states as relationship evidence.
    """

    converged = _mapping(record.report.get("converged_report"), label="converged_report")
    report_version = _string(converged.get("report_version"), label="report_version")
    if report_version != "private-converged-evidence-report-v1":
        raise RelationshipClarityProjectionError(
            "Relationship clarity requires the retained converged evidence report."
        )
    try:
        validate_converged_provenance_references(converged)
    except ConvergedReportReferenceError as exc:
        raise RelationshipClarityProjectionError(
            "Retained converged provenance references are invalid."
        ) from exc

    retained_nodes = _sequence(converged.get("nodes"), label="converged_report.nodes")
    nodes_by_key: dict[str, Mapping[str, object]] = {}
    output_nodes: dict[str, RelationshipNode] = {}
    for value in retained_nodes:
        node = _mapping(value, label="research node")
        node_key = _string(node.get("key"), label="research node key")
        if node_key in nodes_by_key:
            raise RelationshipClarityProjectionError("Research node keys must be unique.")
        kind = _string(node.get("kind"), label="research node kind")
        normalized_value = _string(
            node.get("normalized_value"),
            label="research node normalized_value",
        )
        depth = _index(node.get("depth"), label="research node depth")
        nodes_by_key[node_key] = node
        identifier = RelationshipNode(
            id=_node_id(node_key),
            kind="identifier",
            label=normalized_value,
            research_node_key=node_key,
            depth=depth,
            canonical_identifier=normalized_value,
            identifier_kind=kind,
        )
        output_nodes[identifier.id] = identifier

    m5 = _mapping(converged.get("m5"), label="converged_report.m5")
    if m5.get("calibration_status") != "uncalibrated" or m5.get("is_identity_claim") is not False:
        raise RelationshipClarityProjectionError(
            "Relationship clarity requires uncalibrated, non-identity-claim M5 evidence."
        )
    evaluated_at = _string(m5.get("evaluated_at"), label="M5 evaluated_at")
    evaluations = _sequence(m5.get("evaluations"), label="M5 evaluations")
    edges: list[RelationshipEdge] = []
    case_created_at = record.created_at.isoformat()

    for evaluation_index, evaluation_value in enumerate(evaluations):
        evaluation = _mapping(evaluation_value, label="M5 evaluation")
        if (
            evaluation.get("calibration_status") != "uncalibrated"
            or evaluation.get("is_identity_claim") is not False
        ):
            raise RelationshipClarityProjectionError(
                "Every M5 evaluation must remain uncalibrated and non-probabilistic."
            )
        candidate_key = _string(
            evaluation.get("candidate_node"),
            label="M5 candidate_node",
        )
        if candidate_key not in nodes_by_key:
            raise RelationshipClarityProjectionError(
                "M5 candidate_node does not resolve to a retained research node."
            )
        candidate_observation_index = _index(
            evaluation.get("candidate_observation_index"),
            label="M5 candidate_observation_index",
        )
        candidate_observations = _sequence(
            nodes_by_key[candidate_key].get("observations"),
            label="candidate observations",
        )
        if candidate_observation_index >= len(candidate_observations):
            raise RelationshipClarityProjectionError(
                "M5 candidate observation reference is out of range."
            )
        factors = _sequence(evaluation.get("factors"), label="M5 factors")

        for factor_index, factor_value in enumerate(factors):
            factor = _mapping(factor_value, label="M5 factor")
            try:
                factor_kind = FactorKind(factor.get("kind"))
                factor_status = FactorStatus(factor.get("status"))
            except (TypeError, ValueError) as exc:
                raise RelationshipClarityProjectionError(
                    "Retained M5 factor kind or status is invalid."
                ) from exc
            if factor_status not in _ACTIVE_FACTOR_STATUSES:
                continue

            observation_refs, identifier_refs = _factor_references(factor)
            for identifier_ref in identifier_refs:
                if identifier_ref not in nodes_by_key:
                    raise RelationshipClarityProjectionError(
                        "Factor identifier reference does not resolve to a retained node."
                    )

            resolved_refs: list[str] = []
            provenance: list[RelationshipProvenance] = []
            observation_nodes: list[RelationshipNode] = []
            for observation_ref in observation_refs:
                ref, observation_node, provenance_item = _resolve_observation(
                    nodes_by_key,
                    observation_ref,
                    case_created_at=case_created_at,
                )
                resolved_refs.append(ref)
                observation_nodes.append(observation_node)
                provenance.append(provenance_item)
                output_nodes[observation_node.id] = observation_node

            state = _relationship_state(factor_kind, veto=factor.get("veto"))
            rationale = _string(factor.get("rationale"), label="M5 factor rationale")
            source_node_id = (
                _node_id(identifier_refs[0])
                if identifier_refs
                else observation_nodes[0].id
            )
            edges.append(
                RelationshipEdge(
                    id=f"factor:{evaluation_index}:{factor_index}",
                    source_node_id=source_node_id,
                    target_node_id=_node_id(candidate_key),
                    state=state,
                    relationship_reason=rationale,
                    factor_kind=factor_kind,
                    factor_status=factor_status,
                    supporting_observation_refs=(
                        [] if state is RelationshipState.CONTRADICTION else resolved_refs
                    ),
                    contradictory_observation_refs=(
                        resolved_refs if state is RelationshipState.CONTRADICTION else []
                    ),
                    identifier_refs=identifier_refs,
                    provenance=provenance,
                    context={
                        "m5_evaluated_at": evaluated_at,
                        "candidate_node": candidate_key,
                        "candidate_observation_index": candidate_observation_index,
                    },
                )
            )

    return RelationshipClarityProjection(
        version="relationship-clarity-projection-v1",
        case_id=record.id,
        case_created_at=case_created_at,
        generated_from_report_version=report_version,
        deterministic=True,
        probabilistic=False,
        relationship_states=("corroborated", "unresolved", "contradiction"),
        nodes=sorted(output_nodes.values(), key=lambda item: item.id),
        edges=edges,
    )
