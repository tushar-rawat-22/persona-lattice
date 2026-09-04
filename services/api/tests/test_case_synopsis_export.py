# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
import stat

import pytest

from app.case_synopsis import render_case_synopsis, write_case_synopsis_export


def _payload() -> dict[str, object]:
    return {
        "synopsis_version": "analyst-case-synopsis-v1",
        "case": {"id": "11111111-1111-4111-8111-111111111111", "seed_kind": "username"},
        "evidence_summary": {
            "observation_count": 2,
            "identity_probability": None,
            "identity_claim": False,
        },
        "method_limits": ["Same-handle overlap is not identity proof."],
    }


def test_export_is_owner_only_and_sha256_verifiable(tmp_path) -> None:
    destination = tmp_path / "case-handoff.json"
    payload = _payload()

    digest = write_case_synopsis_export(payload, destination, pretty=True)

    content = destination.read_bytes()
    checksum_path = tmp_path / "case-handoff.json.sha256"
    assert hashlib.sha256(content).hexdigest() == digest
    assert checksum_path.read_text(encoding="ascii") == f"{digest}  case-handoff.json\n"
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert stat.S_IMODE(checksum_path.stat().st_mode) == 0o600
    assert json.loads(content) == payload


def test_render_is_deterministic_regardless_of_mapping_insertion_order() -> None:
    left = {"b": 2, "a": {"z": 1, "y": 0}}
    right = {"a": {"y": 0, "z": 1}, "b": 2}

    assert render_case_synopsis(left) == render_case_synopsis(right)
    assert hashlib.sha256(render_case_synopsis(left)).digest() == hashlib.sha256(
        render_case_synopsis(right)
    ).digest()


def test_export_refuses_missing_parent_without_creating_partial_artifact(tmp_path) -> None:
    destination = tmp_path / "missing" / "case-handoff.json"

    with pytest.raises(ValueError, match="parent directory"):
        write_case_synopsis_export(_payload(), destination)

    assert not destination.exists()
    assert not destination.with_name("case-handoff.json.sha256").exists()
