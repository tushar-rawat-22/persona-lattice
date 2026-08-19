# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

from app.correlation import CorrelationEngine, CorrelationOutcome, CorrelationRequest, FactorKind
from app.correlation.types import CorrelationResult

from .m10_factor_ablation import (
    M10FactorAblationPlan,
    validate_m10_factor_ablation_plan,
)

_EXECUTION_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class M10FactorAblationCase:
    """One controlled M5 request evaluated under every omission scenario."""

    name: str
    request: CorrelationRequest


@dataclass(frozen=True, slots=True)
class M10FactorAblationScenarioResult:
    """Observed M5 change after omitting one factor kind from one controlled case."""

    scenario_name: str
    omitted_factor_kind: FactorKind
    diagnostic_only: bool
    safety_critical: bool
    factor_present: bool
    ablated_outcome: CorrelationOutcome
    ablated_evidence_score: int
    ablated_positive_independence_groups: int
    evidence_score_delta: int
    positive_independence_groups_delta: int


@dataclass(frozen=True, slots=True)
class M10FactorAblationCaseResult:
    """Baseline M5 output plus every replay-anchored omission result for one case."""

    name: str
    baseline_outcome: CorrelationOutcome
    baseline_evidence_score: int
    baseline_positive_independence_groups: int
    scenarios: tuple[M10FactorAblationScenarioResult, ...]


@dataclass(frozen=True, slots=True)
class M10FactorAblationExecution:
    """Diagnostic M5 ablation results anchored to an already-validated M10 plan."""

    schema_version: int
    plan_digest: str
    m5_policy_version: str
    m5_policy_digest: str
    cases: tuple[M10FactorAblationCaseResult, ...]


def _validate_cases(cases: tuple[M10FactorAblationCase, ...]) -> None:
    if not cases:
        raise ValueError("At least one controlled M10 factor-ablation case is required.")
    names: set[str] = set()
    for case in cases:
        if not case.name or case.name.strip() != case.name:
            raise ValueError("M10 factor-ablation case names must be non-empty and trimmed.")
        if case.name in names:
            raise ValueError("M10 factor-ablation case names must be unique.")
        names.add(case.name)
        if len(case.request.factors) < 2:
            raise ValueError(
                "M10 factor-ablation cases require at least two factors so every omission remains a valid M5 request."
            )


def _correlate_without_retaining(
    engine: CorrelationEngine,
    request: CorrelationRequest,
) -> CorrelationResult:
    """Run the real M5 engine while rolling back any diagnostic run/factor records."""

    savepoint = engine.session.begin_nested()
    try:
        return engine.correlate(request)
    finally:
        savepoint.rollback()


def execute_m10_factor_ablation_plan(
    *,
    plan: M10FactorAblationPlan,
    engine: CorrelationEngine,
    cases: Iterable[M10FactorAblationCase],
) -> M10FactorAblationExecution:
    """Execute diagnostic omissions through the production CorrelationEngine.

    This function does not reproduce M5 scoring rules. It changes only the factor
    inputs supplied to the existing engine and reports the resulting deterministic
    outcome/score/group deltas. Each diagnostic correlation is rolled back to its
    own savepoint so M10 cannot retain ablation runs in the supplied evidence
    database. Safety-critical veto omissions remain diagnostics, never production
    policy candidates.
    """

    validate_m10_factor_ablation_plan(plan)
    prepared_cases = tuple(cases)
    _validate_cases(prepared_cases)

    case_results: list[M10FactorAblationCaseResult] = []
    for case in prepared_cases:
        baseline = _correlate_without_retaining(engine, case.request)
        scenario_results: list[M10FactorAblationScenarioResult] = []
        factor_kinds = {factor.kind for factor in case.request.factors}

        for scenario in plan.scenarios:
            ablated_factors = tuple(
                factor
                for factor in case.request.factors
                if factor.kind is not scenario.omitted_factor_kind
            )
            if not ablated_factors:
                raise ValueError(
                    "M10 factor-ablation omission removed every factor from a controlled case."
                )
            ablated = _correlate_without_retaining(
                engine,
                replace(case.request, factors=ablated_factors),
            )
            scenario_results.append(
                M10FactorAblationScenarioResult(
                    scenario_name=scenario.name,
                    omitted_factor_kind=scenario.omitted_factor_kind,
                    diagnostic_only=scenario.diagnostic_only,
                    safety_critical=scenario.safety_critical,
                    factor_present=scenario.omitted_factor_kind in factor_kinds,
                    ablated_outcome=ablated.outcome,
                    ablated_evidence_score=ablated.evidence_score,
                    ablated_positive_independence_groups=ablated.positive_independence_groups,
                    evidence_score_delta=ablated.evidence_score - baseline.evidence_score,
                    positive_independence_groups_delta=(
                        ablated.positive_independence_groups
                        - baseline.positive_independence_groups
                    ),
                )
            )

        case_results.append(
            M10FactorAblationCaseResult(
                name=case.name,
                baseline_outcome=baseline.outcome,
                baseline_evidence_score=baseline.evidence_score,
                baseline_positive_independence_groups=baseline.positive_independence_groups,
                scenarios=tuple(scenario_results),
            )
        )

    return M10FactorAblationExecution(
        schema_version=_EXECUTION_SCHEMA_VERSION,
        plan_digest=plan.plan_digest,
        m5_policy_version=plan.m5_policy_version,
        m5_policy_digest=plan.m5_policy_digest,
        cases=tuple(case_results),
    )
