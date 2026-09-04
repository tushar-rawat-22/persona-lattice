# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib

import pytest

from app.case_synopsis import write_case_synopsis_export
from app.case_synopsis_verify import main, verify_case_synopsis_export


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


def test_verifier_accepts_untampered_export(tmp_path) -> None:
    destination = tmp_path / "case-handoff.json"
    expected = write_case_synopsis_export(_payload(), destination, pretty=True)

    assert verify_case_synopsis_export(destination) == expected


def test_verifier_rejects_export_content_changed_after_generation(tmp_path) -> None:
    destination = tmp_path / "case-handoff.json"
    write_case_synopsis_export(_payload(), destination)
    destination.write_text('{"tampered":true}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="does not match"):
        verify_case_synopsis_export(destination)


def test_verifier_rejects_sidecar_that_names_a_different_file(tmp_path) -> None:
    destination = tmp_path / "case-handoff.json"
    write_case_synopsis_export(_payload(), destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_name("case-handoff.json.sha256").write_text(
        f"{digest}  different-name.json\n",
        encoding="ascii",
    )

    with pytest.raises(ValueError, match="different export file"):
        verify_case_synopsis_export(destination)


def test_verifier_rejects_checksum_valid_non_synopsis_json(tmp_path) -> None:
    destination = tmp_path / "case-handoff.json"
    content = b'{"ordinary":"json"}\n'
    destination.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    destination.with_name("case-handoff.json.sha256").write_text(
        f"{digest}  case-handoff.json\n",
        encoding="ascii",
    )

    with pytest.raises(ValueError, match="synopsis_version"):
        verify_case_synopsis_export(destination)


def test_verifier_rejects_symbolic_link_exports(tmp_path) -> None:
    destination = tmp_path / "case-handoff.json"
    write_case_synopsis_export(_payload(), destination)
    linked = tmp_path / "linked-handoff.json"
    linked.symlink_to(destination)
    linked.with_name("linked-handoff.json.sha256").write_text(
        destination.with_name("case-handoff.json.sha256").read_text(encoding="ascii").replace(
            "case-handoff.json", "linked-handoff.json"
        ),
        encoding="ascii",
    )

    with pytest.raises(ValueError, match="symbolic link"):
        verify_case_synopsis_export(linked)


def test_cli_reports_integrity_without_claiming_authorship(tmp_path, capsys) -> None:
    destination = tmp_path / "case-handoff.json"
    digest = write_case_synopsis_export(_payload(), destination)

    assert main([str(destination)]) == 0
    captured = capsys.readouterr()
    assert f"VERIFIED {digest}  case-handoff.json" in captured.out
    assert "not an authorship signature" in captured.out
    assert captured.err == ""
