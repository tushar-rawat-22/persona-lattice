# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ADMIN_PAGE = ROOT / "apps/web/app/admin/page.tsx"
REVIEW_UI = ROOT / "apps/web/app/admin/upload-review-workflow.tsx"


def test_admin_console_wires_server_owned_upload_review_workflow() -> None:
    page = ADMIN_PAGE.read_text(encoding="utf-8")

    assert 'import { UploadReviewWorkflow } from "./upload-review-workflow";' in page
    assert "<UploadReviewWorkflow" in page
    assert "artifacts={fileResult.artifacts}" in page
    assert "csrfToken={csrfToken}" in page
    assert "purpose={purpose}" in page
    assert "consentAcknowledged={consent}" in page


def test_review_ui_uses_identifier_paths_and_separate_explicit_case_execution() -> None:
    source = REVIEW_UI.read_text(encoding="utf-8")

    for action in ("confirm", "reject", "reopen"):
        assert f'| "{action}"' in source or f'"{action}"' in source
    assert "/v1/files/review/${artifactId}/${candidate.candidate_id}/${action}" in source
    assert "/v1/files/review/${artifactId}/${candidate.candidate_id}/promote" in source
    assert "/v1/files/review/${artifactId}/${candidate.candidate_id}/run-case" in source
    assert 'mode: "converged"' in source
    assert "consent_acknowledged: consentAcknowledged" in source
    assert "No provider was called by promotion." in source


def test_review_mutations_do_not_send_browser_candidate_value_as_authority() -> None:
    source = REVIEW_UI.read_text(encoding="utf-8")

    review_path = "`/v1/files/review/${artifactId}/${candidate.candidate_id}/${action}`"
    promote_path = "`/v1/files/review/${artifactId}/${candidate.candidate_id}/promote`"
    run_path = "`/v1/files/review/${artifactId}/${candidate.candidate_id}/run-case`"
    assert review_path in source
    assert promote_path in source
    assert run_path in source
    assert "body: JSON.stringify({\n            mode:" in source
    assert "candidate.value," not in source
    assert "value: candidate.value" not in source
