# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from email.message import Message
import json
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.providers import dblp_person as dblp
from app.providers.base import ProviderQuery
from app.providers.dblp_person import DblpExactPersonProvider, dblp_person_pid_from_url
from app.providers.errors import (
    ProviderRemoteRateLimitError,
    ProviderResponseTooLarge,
    ProviderResultValidationError,
    ProviderTransientError,
    ProviderValidationError,
)


PID = "65/9612-1"
PID_URL = f"https://dblp.org/pid/{PID}"


def _query(kind: str = "url", value: str = PID_URL) -> ProviderQuery:
    return ProviderQuery(
        subject_id=uuid4(),
        identifier_id=uuid4(),
        identifier_kind=kind,
        identifier_value=value,
    )


def _payload(*, person: str = PID_URL, name: str = "François Gauthier") -> dict[str, object]:
    return {
        "head": {"vars": ["person", "name"]},
        "results": {
            "bindings": [
                {
                    "person": {"type": "uri", "value": person},
                    "name": {"type": "literal", "value": name},
                }
            ]
        },
    }


def test_dblp_url_admission_is_exact_case_sensitive_and_canonical() -> None:
    assert dblp_person_pid_from_url(PID_URL) == PID
    assert dblp_person_pid_from_url("https://dblp.org/pid/l/BarbaraLiskov") == "l/BarbaraLiskov"

    for value in (
        f"http://dblp.org/pid/{PID}",
        f"https://www.dblp.org/pid/{PID}",
        f"https://dblp.org/pid/{PID}/",
        f"https://dblp.org/pid/{PID}.html",
        f"https://dblp.org/pid/{PID}?x=1",
        f"https://dblp.org/pid/{PID}#x",
        f"https://dblp.org:443/pid/{PID}",
        f"https://user:secret@dblp.org/pid/{PID}",
        "https://dblp.org/search/author?q=Gauthier",
        "https://dblp.org/pid/../65/9612",
        "https://dblp.org/pid/65/%2F9612",
    ):
        assert dblp_person_pid_from_url(value) is None


@pytest.mark.asyncio
async def test_success_retains_only_minimal_cc0_person_metadata_and_emits_no_leads() -> None:
    async def fetcher(pid: str) -> dict[str, object]:
        assert pid == PID
        return _payload()

    result = await DblpExactPersonProvider(fetcher=fetcher).execute(_query(), None)

    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.source_locator == PID_URL
    assert observation.payload == {
        "dblp_pid": PID_URL,
        "dblp_primary_name": "François Gauthier",
        "data_license": "CC0",
        "api_attribution": "dblp computer science bibliography",
        "identity_claim": False,
    }
    for excluded in (
        "orcid",
        "affiliation",
        "homepage",
        "publications",
        "coauthors",
        "other_names",
    ):
        assert excluded not in observation.payload

    extraction = extract_observation_leads(
        details=observation.payload,
        source="dblp_exact_person",
        source_locator=observation.source_locator,
    )
    assert extraction.candidates == ()


@pytest.mark.asyncio
async def test_empty_exact_result_is_completed_zero_observation() -> None:
    async def fetcher(pid: str) -> dict[str, object]:
        return {"head": {"vars": ["person", "name"]}, "results": {"bindings": []}}

    result = await DblpExactPersonProvider(fetcher=fetcher).execute(_query(), None)
    assert result.observations == ()


@pytest.mark.asyncio
async def test_provider_rejects_secret_wrong_kind_and_noncanonical_url() -> None:
    provider = DblpExactPersonProvider(fetcher=lambda pid: None)  # type: ignore[arg-type]
    with pytest.raises(ProviderValidationError, match="does not accept credentials"):
        await provider.execute(_query(), "secret")
    with pytest.raises(ProviderValidationError, match="only accepts URLs"):
        await provider.execute(_query(kind="username", value="65/9612"), None)
    with pytest.raises(ProviderValidationError, match="canonical DBLP PID URL"):
        await provider.execute(_query(value=f"{PID_URL}/"), None)


@pytest.mark.asyncio
async def test_mismatch_duplicate_and_invalid_name_fail_closed() -> None:
    async def mismatch(pid: str) -> dict[str, object]:
        return _payload(person="https://dblp.org/pid/08/1510")

    with pytest.raises(ProviderResultValidationError, match="different person resource"):
        await DblpExactPersonProvider(fetcher=mismatch).execute(_query(), None)

    duplicate = _payload()
    results = duplicate["results"]
    assert isinstance(results, dict)
    bindings = results["bindings"]
    assert isinstance(bindings, list)
    bindings.append(bindings[0])

    async def duplicated(pid: str) -> dict[str, object]:
        return duplicate

    with pytest.raises(ProviderResultValidationError, match="not uniquely identified"):
        await DblpExactPersonProvider(fetcher=duplicated).execute(_query(), None)

    async def blank_name(pid: str) -> dict[str, object]:
        return _payload(name=" ")

    with pytest.raises(ProviderResultValidationError, match="invalid primary creator name"):
        await DblpExactPersonProvider(fetcher=blank_name).execute(_query(), None)


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return self.raw[:size]


def test_transport_uses_minimal_exact_sparql_query_and_identifying_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_urlopen(request, timeout: float):
        seen["url"] = request.full_url
        seen["data"] = request.data.decode("utf-8")
        seen["user_agent"] = request.get_header("User-agent")
        seen["accept"] = request.get_header("Accept")
        assert timeout == 4.0
        return _Response(json.dumps(_payload()).encode())

    monkeypatch.setattr(dblp, "urlopen", fake_urlopen)
    assert dblp._fetch_dblp_person_sync(PID) == _payload()
    assert seen["url"] == "https://sparql.dblp.org/sparql"
    query = str(seen["data"])
    assert PID_URL in query
    assert "primaryCreatorName" in query
    for forbidden in ("orcid", "affiliation", "homepage", "authorOf", "coAuthorWith"):
        assert forbidden not in query
    assert seen["accept"] == "application/sparql-results+json"
    assert "github.com/tushar-rawat-22/persona-lattice" in str(seen["user_agent"])


def test_transport_maps_404_429_transient_and_oversized(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = Message()
    headers["Retry-After"] = "13"

    def not_found(request, timeout: float):
        raise HTTPError(request.full_url, 404, "missing", Message(), None)

    monkeypatch.setattr(dblp, "urlopen", not_found)
    assert dblp._fetch_dblp_person_sync(PID) is None

    def rate_limited(request, timeout: float):
        raise HTTPError(request.full_url, 429, "limited", headers, None)

    monkeypatch.setattr(dblp, "urlopen", rate_limited)
    with pytest.raises(ProviderRemoteRateLimitError) as exc_info:
        dblp._fetch_dblp_person_sync(PID)
    assert exc_info.value.retry_after == 13.0

    def unavailable(request, timeout: float):
        raise HTTPError(request.full_url, 503, "down", Message(), None)

    monkeypatch.setattr(dblp, "urlopen", unavailable)
    with pytest.raises(ProviderTransientError):
        dblp._fetch_dblp_person_sync(PID)

    monkeypatch.setattr(
        dblp,
        "urlopen",
        lambda request, timeout: _Response(b"x" * (dblp._MAX_RAW_RESPONSE_BYTES + 1)),
    )
    with pytest.raises(ProviderResponseTooLarge):
        dblp._fetch_dblp_person_sync(PID)
