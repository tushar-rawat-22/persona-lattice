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
from .frontier import FrontierDecision, FrontierEvaluation, FrontierLimits, LeadFrontier
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
from .source_planner import SourcePlan, build_source_plan

__all__ = [
    "FrontierDecision",
    "FrontierEvaluation",
    "FrontierLimits",
    "LeadCandidate",
    "LeadDisposition",
    "LeadExtractionResult",
    "LeadFrontier",
    "LeadKind",
    "LeadReason",
    "SOURCE_BY_NAME",
    "SOURCE_CATALOG",
    "SourceCapability",
    "SourceCostClass",
    "SourceCredentialClass",
    "SourceMode",
    "SourcePlan",
    "SourceStatus",
    "build_source_plan",
    "extract_observation_leads",
    "sources_for_lead",
]
