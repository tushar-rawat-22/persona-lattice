# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASE_UI = ROOT / "apps/web/app/admin/quick-research.tsx"


def _section(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    return source[start_index : source.index(end, start_index)]


def test_case_opening_is_latest_selection_wins() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    open_case = _section(source, "async function openCase", "async function deleteCase")

    assert "caseContextGeneration = useRef(0)" in source
    assert "const generation = startCaseContextChange();" in open_case
    assert "request(`/v1/cases/${caseId}`)" in open_case
    assert open_case.count("isCurrentCaseContext(generation)") >= 3
    assert "const stored = (await response.json()) as StoredCase;" in open_case
    assert "setActiveCase(stored);" in open_case
    assert 'setError("Stored case could not be loaded.")' in open_case


def test_new_research_invalidates_pending_case_loads() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    submit = _section(source, "async function submit", "async function openCase")

    assert "const generation = startCaseContextChange();" in submit
    assert "if (!isCurrentCaseContext(generation)) return;" in submit
    assert "setActiveCase(stored);" in submit
    assert "if (isCurrentCaseContext(generation))" in submit


def test_destructive_case_actions_invalidate_pending_case_loads() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    delete_one = _section(source, "async function deleteCase", "async function loadOlderCases")
    delete_all = _section(source, "async function deleteAllCases", "const report =")

    assert "const generation = startCaseContextChange();" in delete_one
    assert "const generation = startCaseContextChange();" in delete_all


def test_successful_single_delete_reconciles_navigation_after_context_moves() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    delete_one = _section(source, "async function deleteCase", "async function loadOlderCases")

    assert "if (!response.ok && response.status !== 404)" in delete_one
    assert "if (isCurrentCaseContext(generation))" in delete_one
    assert 'setError("Stored case could not be deleted.")' in delete_one
    assert "setActiveCase((current) =>" in delete_one
    assert "current?.id === caseId ? null : current" in delete_one
    assert "await refreshCases();" in delete_one
    assert delete_one.index("await refreshCases();") > delete_one.index("if (!response.ok && response.status !== 404)")
    assert "if (!isCurrentCaseContext(generation)) return;" not in delete_one


def test_successful_delete_all_reconciles_navigation_without_clearing_newer_context() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    delete_all = _section(source, "async function deleteAllCases", "const report =")

    assert "if (!response.ok)" in delete_all
    assert "if (isCurrentCaseContext(generation))" in delete_all
    assert 'setError("Stored cases could not be deleted.")' in delete_all
    assert "if (isCurrentCaseContext(generation)) setActiveCase(null);" in delete_all
    assert "await refreshCases();" in delete_all
    assert "if (!isCurrentCaseContext(generation)) return;" not in delete_all


def test_summary_refresh_invalidates_stale_older_page_responses() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    refresh = _section(source, "const refreshCases", "useEffect(() =>")
    older = _section(source, "async function loadOlderCases", "async function deleteAllCases")

    assert "caseListGeneration = useRef(0)" in source
    assert "const generation = advanceCaseListGeneration();" in refresh
    assert "setLoadingOlderCases(false);" in refresh
    assert "setNextCaseCursor(null);" in refresh
    assert refresh.count("isCurrentCaseList(generation)") >= 2

    assert "const generation = caseListGeneration.current;" in older
    assert "const cursor = nextCaseCursor;" in older
    assert "encodeURIComponent(cursor)" in older
    assert older.count("isCurrentCaseList(generation)") >= 3
    assert older.index("if (!isCurrentCaseList(generation)) return;") < older.index("if (!response.ok)")
    assert "setNextCaseCursor(response.headers.get(\"X-PersonaLattice-Next-Cursor\"));" in older


def test_stale_older_page_completion_cannot_clear_current_loading_state() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    older = _section(source, "async function loadOlderCases", "async function deleteAllCases")

    assert "finally" in older
    assert "if (isCurrentCaseList(generation))" in older
    assert "setLoadingOlderCases(false);" in older


def test_request_ordering_does_not_change_report_loading_boundary() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    open_case = _section(source, "async function openCase", "async function deleteCase")
    refresh = _section(source, "const refreshCases", "useEffect(() =>")

    assert "request(`/v1/cases/${caseId}`)" in open_case
    assert 'request("/v1/cases?limit=8")' in refresh
    assert "StoredCaseSummary[]" in refresh
    assert "StoredCase[]" not in refresh
