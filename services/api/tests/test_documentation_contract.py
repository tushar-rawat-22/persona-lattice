# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[3]
DECISIONS_DIR = REPO_ROOT / "docs" / "decisions"
ADR_NAME = re.compile(r"^(\d{4})-[a-z0-9][a-z0-9-]*\.md$")


def test_architecture_decision_numbers_are_unique_and_contiguous() -> None:
    numbered: list[tuple[int, str]] = []
    for path in DECISIONS_DIR.glob("*.md"):
        match = ADR_NAME.fullmatch(path.name)
        assert match is not None, f"Unexpected ADR filename: {path.name}"
        numbered.append((int(match.group(1)), path.name))

    assert numbered
    numbers = sorted(number for number, _name in numbered)
    assert len(numbers) == len(set(numbers))
    assert numbers == list(range(1, max(numbers) + 1))
