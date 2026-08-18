# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


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
