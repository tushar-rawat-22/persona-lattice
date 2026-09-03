# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta

import pytest

from app.cases import CASE_STORE
from app.research import ResearchKind


def _configure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PERSONALATTICE_DB_PATH", str(tmp_path / "cursor-scope.sqlite3"))
    monkeypatch.setenv("PERSONALATTICE_CASE_RETENTION_DAYS", "30")


def _seed(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    base = datetime(2026, 9, 3, 8, 0, tzinfo=UTC)
    for index in range(4):
        CASE_STORE.create_payload(
            seed_kind=ResearchKind.DOMAIN,
            seed_value=f"scope-{index}.example",
            report_payload={},
            now=base + timedelta(minutes=index),
        )
    CASE_STORE.create_payload(
        seed_kind=ResearchKind.USERNAME,
        seed_value="scope-user",
        report_payload={},
        now=base + timedelta(minutes=5),
    )
    return base


def test_filtered_cursor_rejects_query_change(monkeypatch, tmp_path) -> None:
    base = _seed(monkeypatch, tmp_path)
    _, cursor = CASE_STORE.list_summaries(
        limit=2,
        query="scope",
        seed_kind=ResearchKind.DOMAIN,
        now=base + timedelta(hours=1),
    )
    assert cursor is not None

    with pytest.raises(ValueError, match="does not match the active search filters"):
        CASE_STORE.list_summaries(
            limit=2,
            cursor=cursor,
            query="example",
            seed_kind=ResearchKind.DOMAIN,
            now=base + timedelta(hours=1),
        )


def test_filtered_cursor_rejects_kind_change(monkeypatch, tmp_path) -> None:
    base = _seed(monkeypatch, tmp_path)
    _, cursor = CASE_STORE.list_summaries(
        limit=2,
        query="scope",
        seed_kind=ResearchKind.DOMAIN,
        now=base + timedelta(hours=1),
    )
    assert cursor is not None

    with pytest.raises(ValueError, match="does not match the active search filters"):
        CASE_STORE.list_summaries(
            limit=2,
            cursor=cursor,
            query="scope",
            seed_kind=ResearchKind.USERNAME,
            now=base + timedelta(hours=1),
        )


def test_cursor_scope_is_case_insensitive_and_whitespace_normalized(monkeypatch, tmp_path) -> None:
    base = _seed(monkeypatch, tmp_path)
    first, cursor = CASE_STORE.list_summaries(
        limit=2,
        query="  SCOPE  ",
        seed_kind=ResearchKind.DOMAIN,
        now=base + timedelta(hours=1),
    )
    assert len(first) == 2
    assert cursor is not None

    second, next_cursor = CASE_STORE.list_summaries(
        limit=2,
        cursor=cursor,
        query="scope",
        seed_kind=ResearchKind.DOMAIN,
        now=base + timedelta(hours=1),
    )
    assert len(second) == 2
    assert next_cursor is None
    assert {item.id for item in first}.isdisjoint(item.id for item in second)


def test_unfiltered_cursor_remains_stable(monkeypatch, tmp_path) -> None:
    base = _seed(monkeypatch, tmp_path)
    first, cursor = CASE_STORE.list_summaries(limit=2, now=base + timedelta(hours=1))
    assert len(first) == 2
    assert cursor is not None

    second, _ = CASE_STORE.list_summaries(
        limit=2,
        cursor=cursor,
        now=base + timedelta(hours=1),
    )
    assert len(second) == 2
    assert {item.id for item in first}.isdisjoint(item.id for item in second)
