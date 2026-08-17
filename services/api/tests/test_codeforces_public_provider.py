# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.providers.base import ProviderQuery
from app.providers.codeforces_public import CodeforcesPublicProfileProvider
from app.providers.errors import ProviderValidationError


def _query(kind: str, value: str) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


@pytest.mark.asyncio
async def test_lookup_admits_only_reviewed_public_fields_and_marks_candidate() -> None:
    async def fetcher(value: str):
        assert value == "tourist"
        return {
            "handle": "tourist",
            "firstName": "Gennady",
            "rating": 3800,
            "organization": "public org",
            "privateToken": "must-not-leak",
        }

    result = await CodeforcesPublicProfileProvider(fetcher=fetcher).execute(
        _query("username", "tourist"),
        None,
    )

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://codeforces.com/profile/tourist"
    assert observation.payload["handle"] == "tourist"
    assert observation.payload["matched_by"] == "exact_handle"
    assert observation.payload["account_candidate"] is True
    assert observation.payload["identity_claim"] is False
    assert "privateToken" not in observation.payload


@pytest.mark.asyncio
async def test_historic_handle_result_stays_candidate_and_is_labeled() -> None:
    async def fetcher(value: str):
        assert value == "old_handle"
        return {"handle": "CurrentHandle", "rating": 2100}

    result = await CodeforcesPublicProfileProvider(fetcher=fetcher).execute(
        _query("username", "old_handle"),
        None,
    )

    observation = result.observations[0]
    assert observation.source_locator == "https://codeforces.com/profile/CurrentHandle"
    assert observation.payload["matched_by"] == "historic_handle"
    assert observation.payload["identity_claim"] is False


@pytest.mark.asyncio
async def test_empty_result_is_valid_not_found() -> None:
    async def fetcher(value: str):
        return None

    result = await CodeforcesPublicProfileProvider(fetcher=fetcher).execute(
        _query("username", "missing"),
        None,
    )
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_credentials_unsupported_kinds_and_missing_handle() -> None:
    async def fetcher(value: str):
        return {}

    provider = CodeforcesPublicProfileProvider(fetcher=fetcher)
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query("username", "tourist"), "secret")
    with pytest.raises(ProviderValidationError, match="usernames only"):
        await provider.execute(_query("email", "person@example.test"), None)
    with pytest.raises(ProviderValidationError, match="missing handle"):
        await provider.execute(_query("username", "tourist"), None)
