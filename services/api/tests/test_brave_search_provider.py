# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import uuid4

import pytest

from app.providers import ProviderQuery, ProviderValidationError
from app.providers.brave_search import BravePublicWebSearchProvider
from app.public_search import PublicSearchResult


def _query(*, kind: str = "username", value: str = "CaseHandle") -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


@pytest.mark.asyncio
async def test_brave_provider_emits_only_bounded_discovery_evidence() -> None:
    async def fetcher(identifier: str, secret: str):
        assert identifier == "CaseHandle"
        assert secret == "server-secret"
        return (
            PublicSearchResult(
                title="Public mention",
                url="https://example.test/profile",
                description="Exact public mention.",
            ),
        )

    result = await BravePublicWebSearchProvider(fetcher=fetcher).execute(
        _query(),
        "server-secret",
    )

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://example.test/profile"
    assert observation.payload == {
        "title": "Public mention",
        "description": "Exact public mention.",
        "exact_identifier_query": True,
        "content_fetched": False,
        "identity_claim": False,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["username", "email", "phone", "url"])
async def test_brave_provider_preserves_existing_supported_seed_kinds(kind: str) -> None:
    async def fetcher(_identifier: str, _secret: str):
        return ()

    result = await BravePublicWebSearchProvider(fetcher=fetcher).execute(
        _query(kind=kind),
        "server-secret",
    )
    assert result.observations == ()


@pytest.mark.asyncio
async def test_brave_provider_rejects_missing_secret_before_fetcher() -> None:
    async def fetcher(_identifier: str, _secret: str):
        raise AssertionError("fetcher must not run")

    with pytest.raises(ProviderValidationError, match="requires a server-side API key"):
        await BravePublicWebSearchProvider(fetcher=fetcher).execute(_query(), None)


@pytest.mark.asyncio
async def test_brave_provider_rejects_unsupported_identifier_kind_before_fetcher() -> None:
    async def fetcher(_identifier: str, _secret: str):
        raise AssertionError("fetcher must not run")

    with pytest.raises(ProviderValidationError, match="does not support"):
        await BravePublicWebSearchProvider(fetcher=fetcher).execute(
            _query(kind="domain"),
            "server-secret",
        )
