# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASE_UI = ROOT / "apps/web/app/admin/quick-research.tsx"


def test_recent_cases_are_typed_as_summaries_not_full_reports() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert "type StoredCaseSummary = {" in source
    assert "type StoredCase = StoredCaseSummary & {" in source
    assert "useState<StoredCaseSummary[]>([])" in source
    assert "as StoredCaseSummary[]" in source

    recent_section = source[source.index('<div className="recentCases">') :]
    assert "recentCases.map" in recent_section
    assert "item.report" not in recent_section


def test_recent_cases_consume_bounded_continuation_cursor() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert 'response.headers.get("X-PersonaLattice-Next-Cursor")' in source
    assert "const [nextCaseCursor, setNextCaseCursor] = useState<string | null>(null);" in source
    assert "async function loadOlderCases()" in source
    assert "encodeURIComponent(nextCaseCursor)" in source
    assert '"Load older cases"' in source
    assert "loadingOlderCases" in source


def test_older_case_pages_append_without_duplicate_ids() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    load_start = source.index("async function loadOlderCases")
    delete_all_start = source.index("async function deleteAllCases")
    load_older = source[load_start:delete_all_start]

    assert "new Set(current.map((item) => item.id))" in load_older
    assert "page.filter((item) => !existingIds.has(item.id))" in load_older
    assert "setNextCaseCursor" in load_older


def test_full_report_is_still_loaded_only_when_case_is_opened() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    open_start = source.index("async function openCase")
    delete_start = source.index("async function deleteCase")
    open_case = source[open_start:delete_start]

    assert "request(`/v1/cases/${caseId}`)" in open_case
    assert "setActiveCase((await response.json()) as StoredCase);" in open_case

    refresh_start = source.index("const refreshCases")
    submit_start = source.index("async function submit")
    refresh = source[refresh_start:submit_start]
    assert 'request("/v1/cases?limit=8")' in refresh
    assert "StoredCaseSummary[]" in refresh
    assert "StoredCase[]" not in refresh
