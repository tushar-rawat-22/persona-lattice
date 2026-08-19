# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from app.correlation.policy import (
    FACTOR_WEIGHTS,
    MIN_STRONG_INDEPENDENCE_GROUPS,
    M5_POLICY_VERSION,
    POSSIBLE_MATCH_THRESHOLD,
    STRONG_CANDIDATE_THRESHOLD,
    STRONG_FACTOR_KINDS,
    VETO_FACTOR_KINDS,
)
from app.correlation.types import FactorKind

from .m10_replay import M10ReplayRecord

_ABLATION_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class M10FactorAblationScenario:
    """One diagnostic omission from the exact current M5 factor vocabulary."""

    name: str
    omitted_factor_kind: FactorKind
    diagnostic_only: bool
    safety_critical: bool


@dataclass(frozen=True, slots=True)
class M10FactorAblationPlan:
    """Replay-anchored manifest for later controlled M5 factor ablations."""

    schema_version: int
    baseline_replay_input_digest: str
    baseline_replay_result_digest: str
    m5_policy_version: str
    m5_policy_digest: str
    scenarios: tuple[M10FactorAblationScenario, ...]
    plan_digest: str


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_digest(value: str, *, field: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field} must be a SHA-256 hex digest.")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be a SHA-256 hex digest.") from exc


def _validate_policy_vocabulary() -> None:
    factor_kinds = set(FactorKind)
    weight_kinds = set(FACTOR_WEIGHTS)
    if weight_kinds != factor_kinds:
        missing = sorted(kind.value for kind in factor_kinds - weight_kinds)
        extra = sorted(kind.value for kind in weight_kinds - factor_kinds)
        raise ValueError(
            "M5 factor weights drift from the factor vocabulary: "
            f"missing={missing!r}, extra={extra!r}."
        )
    if not STRONG_FACTOR_KINDS.issubset(factor_kinds):
        raise ValueError("M5 strong-factor vocabulary contains an unknown factor kind.")
    if not VETO_FACTOR_KINDS.issubset(factor_kinds):
        raise ValueError("M5 veto-factor vocabulary contains an unknown factor kind.")


def _m5_policy_payload() -> dict[str, object]:
    _validate_policy_vocabulary()
    return {
        "policy_version": M5_POLICY_VERSION,
        "factor_weights": [
            [kind.value, FACTOR_WEIGHTS[kind]]
            for kind in sorted(FactorKind, key=lambda item: item.value)
        ],
        "possible_match_threshold": POSSIBLE_MATCH_THRESHOLD,
        "strong_candidate_threshold": STRONG_CANDIDATE_THRESHOLD,
        "min_strong_independence_groups": MIN_STRONG_INDEPENDENCE_GROUPS,
        "strong_factor_kinds": sorted(kind.value for kind in STRONG_FACTOR_KINDS),
        "veto_factor_kinds": sorted(kind.value for kind in VETO_FACTOR_KINDS),
    }


def current_m5_policy_digest() -> str:
    """Return the exact M5 policy identity used by M10 ablation execution."""

    return _sha256_json(_m5_policy_payload())


def _scenario_payload(scenario: M10FactorAblationScenario) -> dict[str, object]:
    return {
        "name": scenario.name,
        "omitted_factor_kind": scenario.omitted_factor_kind.value,
        "diagnostic_only": scenario.diagnostic_only,
        "safety_critical": scenario.safety_critical,
    }


def build_m10_factor_ablation_plan(replay: M10ReplayRecord) -> M10FactorAblationPlan:
    """Build a deterministic omission plan without changing or reimplementing M5.

    The plan identifies the exact frontier replay and exact M5 policy that a later
    ablation execution must use. It does not score candidates, change production
    weights, or authorize any factor removal in production.
    """

    if replay.schema_version != 1:
        raise ValueError("Unsupported M10 replay schema version.")
    _validate_digest(replay.input_digest, field="baseline replay input digest")
    _validate_digest(replay.result_digest, field="baseline replay result digest")

    policy_digest = current_m5_policy_digest()
    scenarios = tuple(
        M10FactorAblationScenario(
            name=f"omit_{kind.value}",
            omitted_factor_kind=kind,
            diagnostic_only=True,
            safety_critical=kind in VETO_FACTOR_KINDS,
        )
        for kind in sorted(FactorKind, key=lambda item: item.value)
    )
    payload = {
        "schema_version": _ABLATION_SCHEMA_VERSION,
        "baseline_replay_input_digest": replay.input_digest,
        "baseline_replay_result_digest": replay.result_digest,
        "m5_policy_version": M5_POLICY_VERSION,
        "m5_policy_digest": policy_digest,
        "scenarios": [_scenario_payload(scenario) for scenario in scenarios],
    }
    return M10FactorAblationPlan(
        schema_version=_ABLATION_SCHEMA_VERSION,
        baseline_replay_input_digest=replay.input_digest,
        baseline_replay_result_digest=replay.result_digest,
        m5_policy_version=M5_POLICY_VERSION,
        m5_policy_digest=policy_digest,
        scenarios=scenarios,
        plan_digest=_sha256_json(payload),
    )
