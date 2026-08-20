# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers.base import ProviderQuery
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)
from app.providers import openalex_author as openalex
from app.providers.openalex_author import OpenAlexExactAuthorProvider, openalex_author_id_from_url


def _query(
    kind: str = "url",
    value: str = "https://openalex.org/A5023888391",
) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _payload(author_id: str = "A5023888391") -> dict[str, object]:
    return {
        "id": f"https://openalex.org/{author_id}",
        "display_name": "Example Scholar",
        "works_count": 17,
        "cited_by_count": 91,
        "orcid": "https://orcid.org/0000-0000-0000-0000",
        "affiliations": [{"institution": {"display_name": "not retained"}}],
        "topics": [{"display_name": "not retained"}],
    }


def test_author_url_admission_is_exact() -> None:
    assert openalex_author_id_from_url("https://openalex.org/A5023888391") == "A5023888391"
    assert openalex_author_id_from_url("https://openalex.org/A5023888391/") == "A5023888391"

    for value in (
        "http://openalex.org/A5023888391",
        "https://openalex.org/W5023888391",
        "https://openalex.org/A0",
        "https://openalex.org/A-not-valid",
        "https://openalex.org/authors/A5023888391",
        "https://openalex.org/A5023888391?x=1",
        "https://openalex.org/A5023888391#x",
        "https://openalex.org:443/A5023888391",
        "https://user:secret@openalex.org/A5023888391",
        "https://www.openalex.org/A5023888391",
        "javascript:alert(1)",
    ):
        assert openalex_author_id_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_bounded_scholarly_metadata_and_emits_no_leads() -> None:
    async def fetcher(author_id: str, secret: str) -> dict[str, object]:
        assert author_id == "A5023888391"
        assert secret == "free-key"
        return _payload()

    result = await OpenAlexExactAuthorProvider(fetcher=fetcher).execute(_query(), "free-key")

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://openalex.org/A5023888391"
    assert observation.payload == {
        "openalex_author_id": "A5023888391",
        "openalex_display_name": "Example Scholar",
        "openalex_works_count": 17,
        "openalex_cited_by_count": 91,
        "data_license": "CC0",
        "api_attribution": "OpenAlex",
        "identity_claim": False,
    }
    for forbidden in ("orcid", "affiliations", "topics"):
        assert forbidden not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="openalex_exact_author",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_author_is_completed_zero_observation_result() -> None:
    async def fetcher(author_id: str, secret: str) -> None:
        return None

    result = await OpenAlexExactAuthorProvider(fetcher=fetcher).execute(_query(), "free-key")
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_missing_secret_wrong_kind_and_non_author_url() -> None:
    provider = OpenAlexExactAuthorProvider(fetcher=lambda author_id, secret: None)  # type: ignore[arg-type]
    with pytest.raises(ProviderValidationError, match="requires a server-side API key"):
        await provider.execute(_query(), None)
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="username", value="A5023888391"), "key")
    with pytest.raises(ProviderValidationError, match="requires an exact author URL"):
        await provider.execute(_query(value="https://openalex.org/W5023888391"), "key")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "missing its canonical id"),
        ({"id": "https://openalex.org/A999", "display_name": "X", "works_count": 1, "cited_by_count": 1}, "different author id"),
        ({"id": "https://openalex.org/A5023888391", "display_name": "", "works_count": 1, "cited_by_count": 1}, "invalid display_name"),
        ({"id": "https://openalex.org/A5023888391", "display_name": "X", "works_count": True, "cited_by_count": 1}, "invalid works_count"),
    ],
)
async def test_malformed_author_results_fail_closed(payload: dict[str, object], message: str) -> None:
    async def fetcher(author_id: str, secret: str) -> dict[str, object]:
        return payload

    with pytest.raises(ProviderResultValidationError, match=message):
        await OpenAlexExactAuthorProvider(fetcher=fetcher).execute(_query(), "key")


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw
        self.headers = Message()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def test_transport_uses_bearer_auth_select_and_never_puts_secret_in_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["authorization"] = request.get_header("Authorization")
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 4.0
        return _Response(json.dumps(_payload()).encode())

    monkeypatch.setattr(openalex, "urlopen", fake_urlopen)
    payload = openalex._fetch_openalex_author_sync("A5023888391", "super-secret")

    assert payload == _payload()
    assert seen["authorization"] == "Bearer super-secret"
    assert "super-secret" not in seen["url"]
    assert seen["url"] == (
        "https://api.openalex.org/authors/A5023888391?"
        "select=id,display_name,works_count,cited_by_count"
    )
    assert seen["user_agent"] == "PersonaLattice/0.0.1 openalex-exact-author-research"


def test_transport_maps_404_429_transient_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(request, timeout: float):
        raise HTTPError(request.full_url, 404, "missing", Message(), None)

    monkeypatch.setattr(openalex, "urlopen", missing)
    assert openalex._fetch_openalex_author_sync("A5023888391", "key") is None

    headers = Message()
    headers["Retry-After"] = "9"

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "rate limited", headers, None)

    monkeypatch.setattr(openalex, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        openalex._fetch_openalex_author_sync("A5023888391", "key")
    assert exc_info.value.retry_after == 9.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "unavailable", Message(), None)

    monkeypatch.setattr(openalex, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        openalex._fetch_openalex_author_sync("A5023888391", "key")

    monkeypatch.setattr(
        openalex,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (openalex._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge, match="exceeded the adapter limit"):
        openalex._fetch_openalex_author_sync("A5023888391", "key")
