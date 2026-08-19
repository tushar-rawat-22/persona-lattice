# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

import pytest

from app.intelligence.m10_consented_runner import (
    evaluate_local_consented_file,
    evaluate_local_consented_payload,
    main,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "cohort_name": "reviewed-cohort-001",
        "fixtures": [
            {
                "name": "case-001",
                "evidence_digest": _digest("external-consent-record-001"),
                "seed": {"id": "seed", "kind": "username", "value": "samplehandle"},
                "nodes": [
                    {
                        "id": "profile",
                        "parent_id": "seed",
                        "kind": "url",
                        "value": "https://example.test/profile/samplehandle",
                        "reason": "public_url",
                        "disposition": "auto_pivot",
                        "source": "reviewed-fixture-source",
                        "source_locator": "https://example.test/evidence/1",
                        "field_name": "profile_url",
                        "relevance": "relevant",
                    }
                ],
            }
        ],
    }


def test_local_consented_runner_produces_aggregate_replay_anchored_output() -> None:
    result = evaluate_local_consented_payload(_payload(), input_digest=_digest("private-input"))

    assert result.schema_version == 1
    assert result.cohort_name_digest == _digest("reviewed-cohort-001")
    assert result.fixture_count == 1
    assert len(result.local_input_digest) == 64
    assert len(result.replay_input_digest) == 64
    assert len(result.replay_result_digest) == 64
    assert len(result.label_manifest_digest) == 64
    assert len(result.analysis_digest) == 64

    scenarios = {item["scenario_name"]: item for item in result.scenarios}
    assert scenarios["production_depth_2_nodes_12"]["admitted_relevant_count"] == 1
    assert scenarios["production_depth_2_nodes_12"]["admitted_wrong_count"] == 0
    assert scenarios["candidate_depth_3_nodes_12"]["admitted_relevant_count"] == 1

    serialized = json.dumps(asdict(result), sort_keys=True)
    assert "reviewed-cohort-001" not in serialized
    assert "samplehandle" not in serialized
    assert "example.test" not in serialized
    assert "external-consent-record-001" not in serialized


def test_local_consented_runner_input_cannot_claim_provenance_basis() -> None:
    payload = _payload()
    payload["basis"] = "independently_reviewed"

    with pytest.raises(ValueError, match="cannot declare its own label provenance basis"):
        evaluate_local_consented_payload(payload, input_digest=_digest("private-input"))


def test_local_consented_runner_rejects_incomplete_labels() -> None:
    payload = _payload()
    payload["fixtures"][0]["nodes"][0].pop("relevance")

    with pytest.raises(ValueError, match="complete labels for every admitted pivot"):
        evaluate_local_consented_payload(payload, input_digest=_digest("private-input"))


def test_local_consented_runner_rejects_child_of_non_executable_node() -> None:
    payload = _payload()
    nodes = payload["fixtures"][0]["nodes"]
    nodes[0]["disposition"] = "display_only"
    nodes[0].pop("relevance")
    nodes.append(
        {
            "id": "illegal-child",
            "parent_id": "profile",
            "kind": "username",
            "value": "otherhandle",
            "reason": "public_username",
            "disposition": "auto_pivot",
            "source": "reviewed-fixture-source",
            "source_locator": "https://example.test/evidence/2",
            "field_name": "username",
            "relevance": "wrong",
        }
    )

    with pytest.raises(ValueError, match="seed or an earlier successful automatic node"):
        evaluate_local_consented_payload(payload, input_digest=_digest("private-input"))


def test_local_consented_runner_rejects_invalid_evidence_digest_and_oversized_file(tmp_path) -> None:
    payload = _payload()
    payload["fixtures"][0]["evidence_digest"] = "not-a-digest"
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        evaluate_local_consented_payload(payload, input_digest=_digest("private-input"))

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * 1_048_577)
    with pytest.raises(ValueError, match="exceeds"):
        evaluate_local_consented_file(oversized)


def test_local_consented_runner_cli_prints_no_fixture_identifiers(tmp_path, capsys) -> None:
    cohort = tmp_path / "cohort.json"
    cohort.write_text(json.dumps(_payload()), encoding="utf-8")

    assert main([str(cohort)]) == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["fixture_count"] == 1
    assert "reviewed-cohort-001" not in captured.out
    assert "samplehandle" not in captured.out
    assert "example.test" not in captured.out
    assert captured.err == ""


def test_local_consented_runner_cli_sanitizes_validation_failure(tmp_path, capsys) -> None:
    payload = _payload()
    payload["fixtures"][0]["nodes"][0]["value"] = "secret-person-value"
    payload["fixtures"][0]["nodes"][0]["kind"] = "unsupported-kind"
    cohort = tmp_path / "cohort.json"
    cohort.write_text(json.dumps(payload), encoding="utf-8")

    assert main([str(cohort)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "M10 consented cohort validation failed.\n"
    assert "secret-person-value" not in captured.err
    assert "unsupported-kind" not in captured.err
