# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.providers.base import ProviderQuery
from app.providers.errors import ProviderValidationError
from app.providers.gitlab_public import GitLabPublicProfileProvider, gitlab_project_path_from_url


def _url_query(value: str) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind="url",
        identifier_value=value,
    )


def test_subgroup_project_url_admission_is_exact_and_route_safe() -> None:
    assert (
        gitlab_project_path_from_url("https://gitlab.com/engineering/docs/workflows")
        == "engineering/docs/workflows"
    )
    assert (
        gitlab_project_path_from_url("https://gitlab.com/group/subgroup/deeper/project")
        == "group/subgroup/deeper/project"
    )

    rejected = (
        "https://gitlab.com/group/subgroup/project/",
        "https://gitlab.com/group//project",
        "https://gitlab.com/group/subgroup/project.git",
        "https://gitlab.com/group/subgroup/project?x=1",
        "https://gitlab.com/group/subgroup/project#readme",
        "https://gitlab.com/group/subgroup/project/-/issues",
        "https://gitlab.com/group/subgroup/project/-/tree/main",
        "https://gitlab.com/o/acme/group/project",
        "https://gitlab.com/group/./project",
        "https://gitlab.com/group/-/project",
        "https://user:pass@gitlab.com/group/subgroup/project",
        "https://gitlab.com:443/group/subgroup/project",
    )
    assert all(gitlab_project_path_from_url(value) is None for value in rejected)


@pytest.mark.asyncio
async def test_subgroup_project_uses_full_namespace_and_retains_zero_lead_metadata() -> None:
    requested = "https://gitlab.com/engineering/docs/workflows"

    async def fetcher(kind: str, value: str):
        assert (kind, value) == ("url", requested)
        return {
            "id": 4242,
            "path_with_namespace": "engineering/docs/workflows",
            "visibility": "public",
            "archived": False,
            "web_url": requested,
            "namespace": {
                "kind": "group",
                "full_path": "engineering/docs",
                "name": "Docs",
            },
            "owner": {"username": "must-not-become-a-lead"},
            "description": "must not be retained",
        }

    result = await GitLabPublicProfileProvider(fetcher=fetcher).execute(_url_query(requested), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == requested
    assert observation.payload == {
        "gitlab_project_id": 4242,
        "gitlab_project_path_with_namespace": "engineering/docs/workflows",
        "gitlab_project_visibility": "public",
        "gitlab_project_namespace_kind": "group",
        "gitlab_project_namespace_full_path": "engineering/docs",
        "gitlab_project_archived": False,
        "identity_claim": False,
        "field_visibility": "public_project_api",
        "matched_by": "exact_project_url",
    }
    assert "owner" not in observation.payload
    assert "description" not in observation.payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "id": 4242,
                "path_with_namespace": "engineering/docs/workflows",
                "visibility": "public",
                "web_url": "https://gitlab.com/engineering/docs/workflows",
                "namespace": {"kind": "group", "full_path": "engineering"},
            },
            "namespace does not match",
        ),
        (
            {
                "id": 4242,
                "path_with_namespace": "engineering/other/workflows",
                "visibility": "public",
                "web_url": "https://gitlab.com/engineering/other/workflows",
                "namespace": {"kind": "group", "full_path": "engineering/other"},
            },
            "path does not match",
        ),
        (
            {
                "id": 4242,
                "path_with_namespace": "engineering/docs/workflows",
                "visibility": "public",
                "web_url": "https://gitlab.com/engineering/docs/other",
                "namespace": {"kind": "group", "full_path": "engineering/docs"},
            },
            "invalid canonical project URL",
        ),
    ],
)
async def test_subgroup_response_mismatch_fails_closed(
    payload: dict[str, object],
    message: str,
) -> None:
    async def fetcher(kind: str, value: str):
        return payload

    provider = GitLabPublicProfileProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match=message):
        await provider.execute(
            _url_query("https://gitlab.com/engineering/docs/workflows"),
            None,
        )
