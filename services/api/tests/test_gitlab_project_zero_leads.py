# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.extractor import extract_observation_leads


def test_gitlab_project_metadata_emits_no_recursive_leads() -> None:
    details = {
        "gitlab_project_id": 42,
        "gitlab_project_path_with_namespace": "example/project",
        "gitlab_project_visibility": "public",
        "gitlab_project_namespace_kind": "group",
        "gitlab_project_namespace_full_path": "example",
        "gitlab_project_archived": False,
        "identity_claim": False,
        "field_visibility": "public_project_api",
        "matched_by": "exact_project_url",
    }

    result = extract_observation_leads(
        details=details,
        source="gitlab_public_api",
        source_locator="https://gitlab.com/example/project",
    )

    assert result.candidates == ()
    assert result.blocked_field_names == ()
