# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from app.launch_preflight import LaunchPreflightError, _persistent_database_path


def test_preflight_rejects_database_symlink(tmp_path: Path) -> None:
    target = tmp_path / "real.db"
    target.touch()
    link = tmp_path / "linked.db"
    link.symlink_to(target)

    with pytest.raises(LaunchPreflightError, match="must not be a symbolic link"):
        _persistent_database_path({"PERSONALATTICE_DB_PATH": str(link)})


def test_preflight_rejects_non_regular_database_leaf(tmp_path: Path) -> None:
    directory_leaf = tmp_path / "cases.db"
    directory_leaf.mkdir()

    with pytest.raises(LaunchPreflightError, match="must reference a regular file"):
        _persistent_database_path({"PERSONALATTICE_DB_PATH": str(directory_leaf)})


def test_preflight_accepts_missing_database_leaf_in_private_parent(tmp_path: Path) -> None:
    database = tmp_path / "cases.db"

    assert _persistent_database_path({"PERSONALATTICE_DB_PATH": str(database)}) == database
    assert not database.exists()
