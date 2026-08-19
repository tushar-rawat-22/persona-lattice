# SPDX-License-Identifier: Apache-2.0
import re
from pathlib import Path

from app.research import ResearchKind


ROOT = Path(__file__).resolve().parents[3]
CASE_UI = ROOT / "apps/web/app/admin/quick-research.tsx"


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

    summary_start = source.index("function SourceRunSummary")
    summary_end = source.index("export function QuickResearch")
    summary = source[summary_start:summary_end]
    assert ".warnings" not in summary
    assert "warning" not in summary.casefold()


def test_source_visibility_ui_does_not_recreate_provider_policy() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert "execution_attempted ?" in source
    assert "item.state" in source
    assert "item.reason" in source
    assert "aggregate.local_budget_stop_count" in source
    assert "aggregate.optional_not_configured_count" in source
    assert "identity probability" not in source[source.index("function SourceRunSummary"):source.index("export function QuickResearch")].casefold()


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
