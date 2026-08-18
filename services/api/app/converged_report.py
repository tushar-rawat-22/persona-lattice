# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, Sequence


class ConvergedReportReferenceError(ValueError):
    """Raised when retained converged-report references cannot be proven valid."""


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ConvergedReportReferenceError(f"{label} must be an object.")
    return value


def _sequence(value: object, *, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ConvergedReportReferenceError(f"{label} must be an array.")
    return value


def _non_negative_index(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ConvergedReportReferenceError(f"{label} must be a non-negative integer.")
    return value


def _node_by_key(report: Mapping[str, object], node_key: object) -> Mapping[str, object]:
    if not isinstance(node_key, str) or not node_key:
        raise ConvergedReportReferenceError("Referenced node key must be a non-empty string.")
    nodes = _sequence(report.get("nodes"), label="nodes")
    matches = [
        _mapping(node, label="node")
        for node in nodes
        if isinstance(node, Mapping) and node.get("key") == node_key
    ]
    if len(matches) != 1:
        raise ConvergedReportReferenceError(
            f"Referenced node {node_key!r} must resolve exactly once."
        )
    return matches[0]


def resolve_decision_source_observation(
    report: Mapping[str, object],
    decision: Mapping[str, object],
) -> Mapping[str, object]:
    """Resolve one retained lead decision to its canonical parent observation."""

    parent = _node_by_key(report, decision.get("parent_key"))
    observations = _sequence(parent.get("observations"), label="node observations")
    observation_index = _non_negative_index(
        decision.get("source_observation_index"),
        label="source_observation_index",
    )
    if observation_index >= len(observations):
        raise ConvergedReportReferenceError("source_observation_index is out of range.")
    observation = _mapping(
        observations[observation_index],
        label="source observation",
    )
    source = observation.get("source")
    source_locator = observation.get("source_locator")
    if not isinstance(source, str) or not source:
        raise ConvergedReportReferenceError("Canonical source observation is missing source.")
    if not isinstance(source_locator, str) or not source_locator:
        raise ConvergedReportReferenceError(
            "Canonical source observation is missing source_locator."
        )
    return observation


def resolve_edge_decision(
    report: Mapping[str, object],
    edge: Mapping[str, object],
) -> Mapping[str, object]:
    """Resolve one retained edge to its canonical admitted lead decision."""

    lead_graph = _mapping(report.get("lead_graph"), label="lead_graph")
    decisions = _sequence(lead_graph.get("decisions"), label="lead_graph.decisions")
    decision_index = _non_negative_index(
        edge.get("lead_decision_index"),
        label="lead_decision_index",
    )
    if decision_index >= len(decisions):
        raise ConvergedReportReferenceError("lead_decision_index is out of range.")
    decision = _mapping(decisions[decision_index], label="lead decision")
    if decision.get("decision") != "admitted":
        raise ConvergedReportReferenceError("Edge must reference an admitted lead decision.")
    for field in ("parent_key", "child_key", "reason"):
        if edge.get(field) != decision.get(field):
            raise ConvergedReportReferenceError(
                f"Edge {field} does not match its admitted lead decision."
            )
    resolve_decision_source_observation(report, decision)
    return decision


def validate_converged_provenance_references(report: Mapping[str, object]) -> None:
    """Fail closed if new retained provenance references do not resolve exactly."""

    lead_graph = _mapping(report.get("lead_graph"), label="lead_graph")
    decisions = _sequence(lead_graph.get("decisions"), label="lead_graph.decisions")
    for item in decisions:
        decision = _mapping(item, label="lead decision")
        if "source" in decision or "source_locator" in decision:
            raise ConvergedReportReferenceError(
                "New lead decisions must reference canonical observations instead of copying provenance."
            )
        resolve_decision_source_observation(report, decision)

    edges = _sequence(report.get("edges"), label="edges")
    for item in edges:
        edge = _mapping(item, label="edge")
        if "source" in edge or "source_locator" in edge:
            raise ConvergedReportReferenceError(
                "New edges must reference admitted lead decisions instead of copying provenance."
            )
        resolve_edge_decision(report, edge)
