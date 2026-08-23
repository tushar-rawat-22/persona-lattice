# SPDX-License-Identifier: Apache-2.0
import re
from pathlib import Path

from app.research import ResearchKind


ROOT = Path(__file__).resolve().parents[3]
CASE_UI = ROOT / "apps/web/app/admin/quick-research.tsx"


def _source_run_summary(source: str) -> str:
    start = source.index("function SourceRunSummary")
    end = source.index("function M5EvidenceTable", start)
    return source[start:end]


def test_private_case_view_reads_retained_seed_provenance_directly() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert "seed_provenance?: SeedProvenance;" in source
    assert "report.seed_provenance &&" in source
    assert "Reviewed document seed" in source
    assert "report.seed_provenance.source_locator" in source
    assert "report.seed_provenance.human_reviewed" in source


def test_private_case_view_reads_typed_source_runs_without_warning_inference() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert "source_runs?: SourceRunReport;" in source
    assert "sourceRuns.records.map" in source
    assert "sourceRuns.evaluation?.aggregate" in source
    assert "node.source_runs" in source
    assert "report.source_runs" in source
    assert "Source execution state is unavailable for this historical case." in source

    summary = _source_run_summary(source)
    assert ".warnings" not in summary
    assert "warning" not in summary.casefold()


def test_source_visibility_ui_does_not_recreate_provider_policy() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert "execution_attempted ?" in source
    assert "item.state" in source
    assert "item.reason" in source
    assert "aggregate.local_budget_stop_count" in source
    assert "aggregate.optional_not_configured_count" in source
    assert "identity probability" not in _source_run_summary(source).casefold()


def test_private_case_view_explains_missing_evidence_from_retained_counters() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    for field in (
        "withheld_count: number;",
        "public_web_opt_out_count: number;",
        "account_unavailable_count: number;",
        "routing_unavailable_count: number;",
    ):
        assert field in source

    details_start = source.index("function sourceOutcomeDetails")
    details_end = source.index("function resolveConnectedIdentifier")
    details = source[details_start:details_end]
    assert "aggregate.public_web_opt_out_count" in details
    assert "aggregate.account_unavailable_count" in details
    assert "aggregate.remote_rate_limit_count" in details
    assert "aggregate.execution_failure_count" in details
    assert "aggregate.malformed_result_count" in details
    assert "aggregate.routing_unavailable_count" in details
    assert "aggregate.local_budget_stop_count" in details
    assert "aggregate.optional_not_configured_count" in details
    assert "aggregate.missing_secret_config_count" in details
    assert "aggregate.provider_policy_block_count" in details
    assert "routing authority unavailable · no provider attempt" in details
    assert "provider attempt failed" in details

    summary = _source_run_summary(source)
    assert "Why evidence may be missing" in summary
    assert "sourceOutcomeDetails(aggregate)" in summary
    assert "aggregate.withheld_count" in summary
    assert ".warnings" not in summary


def test_private_quick_research_exposes_every_live_backend_research_kind() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    type_match = re.search(r"type ResearchKind = (?P<body>[^;]+);", source)
    assert type_match is not None
    ui_type_kinds = set(re.findall(r'"([a-z_]+)"', type_match.group("body")))

    selector_start = source.index("Starting identifier")
    selector_end = source.index("</select>", selector_start)
    selector = source[selector_start:selector_end]
    selector_kinds = set(re.findall(r'<option value="([a-z_]+)">', selector))

    backend_kinds = {kind.value for kind in ResearchKind}
    assert ui_type_kinds == backend_kinds
    assert selector_kinds == backend_kinds


def test_private_domain_research_is_explicit_and_uses_existing_case_views() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert '<option value="domain">Domain</option>' in source
    assert 'domain: "example.com"' in source
    assert "Domain research is explicit-seed only" in source
    assert "domain clues discovered during another case remain display-only" in source
    assert '"/v1/cases/run-converged"' in source
    assert "kind," in source[source.index('"/v1/cases/run-converged"'):source.index("const body =", source.index('"/v1/cases/run-converged"'))]

    # DOMAIN cases use the same retained-case, source-state and provenance views as other kinds.
    assert "activeCase.seed_kind.toUpperCase()" in source
    assert "<strong>{node.kind} · {node.normalized_value}</strong>" in source
    assert "sourceRuns={node.source_runs}" in source
    assert "observation.source_locator" in source


def test_private_case_view_explains_which_canonical_observation_field_caused_a_pivot() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert "type ResolvedPivotProvenance" in source
    assert "source_field: string | null;" in source
    assert "observation_summary: string | null;" in source
    assert "source_field: decision.source_field" in source
    assert "observation_summary: nonEmptyString(observation.summary) ? observation.summary : null" in source
    assert "field ${provenance.source_field}" in source
    assert "provenance.observation_summary" in source
    assert "provenance.source_locator" in source

    resolver_start = source.index("function resolveEdgeProvenance")
    resolver_end = source.index("function SourceRunSummary")
    resolver = source[resolver_start:resolver_end]

    # The UI must resolve the exact canonical decision/observation reference and fail closed on drift.
    assert 'decision.decision !== "admitted"' in resolver
    assert "decision.parent_key !== edge.parent_key" in resolver
    assert "decision.child_key !== edge.child_key" in resolver
    assert "decision.reason !== edge.reason" in resolver
    assert "decision.source_observation_index" in resolver
    assert "decision.source_field" in resolver
    assert "decision.source_field in observation.details" in resolver
    assert "return null" in resolver


def test_private_case_view_explains_m5_factor_contributions_without_recomputing_m5() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    m5_start = source.index("<h3>M5 evidence-strength triage</h3>")
    m5_end = source.index("<h3>Evidence pivots</h3>")
    m5 = source[m5_start:m5_end]

    assert "candidate?.source_locator" in m5
    assert "evaluation.candidate_source_locator" in m5
    assert "evaluation.positive_independence_groups" in m5
    assert "evaluation.policy_version" in m5
    assert "factor.independence_group" in m5
    assert "factor.base_weight" in m5
    assert "factor.applied_weight" in m5
    assert "factor.status" in m5
    assert "factor.rationale" in m5
    assert "factor.veto" in m5
    assert "not an identity probability" in m5

    # The operator surface consumes retained M5 output. It must not reproduce policy math or thresholds.
    assert "possible_match" not in m5
    assert "strong_candidate" not in m5
    assert "hard_contradiction" not in m5
