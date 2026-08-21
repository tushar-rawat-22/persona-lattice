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
from app.providers import crossref_work as crossref
from app.providers.crossref_work import CrossrefExactWorkProvider, crossref_doi_from_url


def _query(
    kind: str = "url",
    value: str = "https://doi.org/10.1038/s41586-020-2649-2",
) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _payload(doi: str = "10.1038/s41586-020-2649-2") -> dict[str, object]:
    return {
        "status": "ok",
        "message-type": "work",
        "message-version": "1.0.0",
        "message": {
            "DOI": doi,
            "title": ["A bounded publication title"],
            "published-print": {"date-parts": [[2020, 9, 3]]},
            "author": [
                {"given": "Ada", "family": "Example", "ORCID": "https://orcid.org/0000-0000-0000-0000"},
                {"name": "Example Consortium", "affiliation": [{"name": "not retained"}]},
            ],
            "abstract": "not retained",
            "reference": [{"DOI": "10.1000/not-retained"}],
            "funder": [{"name": "not retained"}],
            "link": [{"URL": "https://example.invalid/fulltext"}],
            "subject": ["not retained"],
        },
    }


def test_doi_url_admission_is_exact_and_percent_safe() -> None:
    assert crossref_doi_from_url("https://doi.org/10.1038/s41586-020-2649-2") == "10.1038/s41586-020-2649-2"
    assert crossref_doi_from_url("https://doi.org/10.5555%2FABC%28123%29") == "10.5555/ABC(123)"

    for value in (
        "http://doi.org/10.1038/s41586-020-2649-2",
        "https://dx.doi.org/10.1038/s41586-020-2649-2",
        "https://doi.org/",
        "https://doi.org/not-a-doi",
        "https://doi.org/10.12/x",
        "https://doi.org/10.1234/",
        "https://doi.org/10.1234/x?download=1",
        "https://doi.org/10.1234/x#fragment",
        "https://doi.org:443/10.1234/x",
        "https://user:secret@doi.org/10.1234/x",
        "https://doi.org/10.1234%2",
        "javascript:alert(1)",
    ):
        assert crossref_doi_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_bounded_bibliographic_metadata_and_emits_no_leads() -> None:
    async def fetcher(doi: str) -> dict[str, object]:
        assert doi == "10.1038/s41586-020-2649-2"
        return _payload()

    result = await CrossrefExactWorkProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == "https://doi.org/10.1038/s41586-020-2649-2"
    assert observation.payload == {
        "crossref_doi": "10.1038/s41586-020-2649-2",
        "crossref_title": "A bounded publication title",
        "crossref_author_names": ["Ada Example", "Example Consortium"],
        "author_names_display_only": True,
        "api_attribution": "Crossref",
        "identity_claim": False,
        "crossref_publication_year": 2020,
    }
    for forbidden in ("ORCID", "affiliation", "abstract", "reference", "funder", "link", "subject"):
        assert forbidden not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="crossref_exact_work",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_missing_work_is_completed_zero_observation_result() -> None:
    async def fetcher(doi: str) -> None:
        return None

    result = await CrossrefExactWorkProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_secret_wrong_kind_and_non_doi_url() -> None:
    provider = CrossrefExactWorkProvider(fetcher=lambda doi: None)  # type: ignore[arg-type]
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="username", value="10.1038/s41586-020-2649-2"), None)
    with pytest.raises(ProviderValidationError, match="requires an exact DOI URL"):
        await provider.execute(_query(value="https://example.com/10.1038/s41586-020-2649-2"), None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "invalid singleton envelope"),
        ({"status": "ok", "message-type": "work", "message": {}}, "missing its DOI"),
        ({"status": "ok", "message-type": "work", "message": {"DOI": "10.9999/other", "title": ["X"]}}, "different DOI"),
        ({"status": "ok", "message-type": "work", "message": {"DOI": "10.1038/s41586-020-2649-2", "title": []}}, "missing a title"),
    ],
)
async def test_malformed_work_results_fail_closed(payload: dict[str, object], message: str) -> None:
    async def fetcher(doi: str) -> dict[str, object]:
        return payload

    with pytest.raises(ProviderResultValidationError, match=message):
        await CrossrefExactWorkProvider(fetcher=fetcher).execute(_query(), None)


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


def test_transport_uses_singleton_endpoint_and_escapes_reserved_doi_characters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 4.0
        return _Response(json.dumps(_payload("10.5555/ABC(123)"), separators=(",", ":")).encode())

    monkeypatch.setattr(crossref, "urlopen", fake_urlopen)
    payload = crossref._fetch_crossref_work_sync("10.5555/ABC(123)")

    assert payload == _payload("10.5555/ABC(123)")
    assert seen["url"] == "https://api.crossref.org/works/10.5555%2FABC%28123%29"
    assert "?" not in seen["url"]
    assert seen["user_agent"] == "PersonaLattice/0.0.1 crossref-exact-doi-research"


def test_transport_maps_404_429_transient_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(request, timeout: float):
        raise HTTPError(request.full_url, 404, "missing", Message(), None)

    monkeypatch.setattr(crossref, "urlopen", missing)
    assert crossref._fetch_crossref_work_sync("10.1234/example") is None

    headers = Message()
    headers["Retry-After"] = "7"

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "rate limited", headers, None)

    monkeypatch.setattr(crossref, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        crossref._fetch_crossref_work_sync("10.1234/example")
    assert exc_info.value.retry_after == 7.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "unavailable", Message(), None)

    monkeypatch.setattr(crossref, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        crossref._fetch_crossref_work_sync("10.1234/example")

    monkeypatch.setattr(
        crossref,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (crossref._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge, match="exceeded the adapter limit"):
        crossref._fetch_crossref_work_sync("10.1234/example")
