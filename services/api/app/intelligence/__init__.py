# SPDX-License-Identifier: Apache-2.0
"""Evidence-lead graph contracts for recursive public/authorized research."""

from .contracts import (
    LeadCandidate,
    LeadDisposition,
    LeadExtractionResult,
    LeadKind,
    LeadReason,
)
from .extractor import extract_observation_leads
from .frontier import (
    FrontierDecision,
    FrontierEvaluation,
    FrontierLimits,
    LeadFrontier,
    compatibility_frontier_limits,
)
from .graph_evaluation import (
    GraphEvaluationCounters,
    PivotRelevance,
    build_graph_evaluation_counters,
)
from .graph_limit_evaluation import (
    GraphFixtureLead,
    GraphLimitComparison,
    GraphLimitDelta,
    GraphLimitScenario,
    GraphLimitScenarioResult,
    compare_graph_limit_fixture,
    evaluate_graph_limit_fixture,
)
from .source_bindings import (
    SOURCE_BINDING_BY_NAME,
    SOURCE_BINDINGS,
    SourceBinding,
    SourceBindingError,
    SourceExecutionBackend,
    source_binding_for,
    validate_source_bindings,
)
from .source_catalog import (
    SOURCE_BY_NAME,
    SOURCE_CATALOG,
    SourceCapability,
    SourceCostClass,
    SourceCredentialClass,
    SourceMode,
    SourceStatus,
    sources_for_lead,
)
from .source_evaluation import build_source_evaluation_counters
from .source_planner import SourcePlan, build_source_plan
from .source_states import SourceRunReason, SourceRunRecord, SourceRunState

__all__ = [
    "FrontierDecision",
    "FrontierEvaluation",
    "FrontierLimits",
    "GraphEvaluationCounters",
    "GraphFixtureLead",
    "GraphLimitComparison",
    "GraphLimitDelta",
    "GraphLimitScenario",
    "GraphLimitScenarioResult",
    "LeadCandidate",
    "LeadDisposition",
    "LeadExtractionResult",
    "LeadFrontier",
    "LeadKind",
    "LeadReason",
    "PivotRelevance",
    "SOURCE_BINDING_BY_NAME",
    "SOURCE_BINDINGS",
    "SOURCE_BY_NAME",
    "SOURCE_CATALOG",
    "SourceBinding",
    "SourceBindingError",
    "SourceCapability",
    "SourceCostClass",
    "SourceCredentialClass",
    "SourceExecutionBackend",
    "SourceMode",
    "SourcePlan",
    "SourceRunReason",
    "SourceRunRecord",
    "SourceRunState",
    "SourceStatus",
    "build_graph_evaluation_counters",
    "build_source_evaluation_counters",
    "build_source_plan",
    "compare_graph_limit_fixture",
    "compatibility_frontier_limits",
    "evaluate_graph_limit_fixture",
    "extract_observation_leads",
    "source_binding_for",
    "sources_for_lead",
    "validate_source_bindings",
]
