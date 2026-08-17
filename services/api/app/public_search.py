# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from .evidence import IdentifierKind
from .models import Purpose
from .providers.base import ProviderQuery
from .providers.contracts import ExecutionRequest


_MAX_QUERY_CHARS = 300
_MAX_RESULTS = 10
_RESULT_TEXT_CHARS = 600


@dataclass(frozen=True, slots=True)
class PublicSearchResult:
    title: str
    url: str
    description: str


def _api_key() -> str | None:
    value = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()
    return value or None


def public_search_configured() -> bool:
    return _api_key() is not None


def _bounded_text(value: object, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _canonical_public_result_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value.strip())
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return None
        if parts.username or parts.password:
            return None
        port = parts.port
    except ValueError:
        return None
    hostname = parts.hostname.lower()
    if port is not None and not (
        (parts.scheme.lower() == "https" and port == 443)
        or (parts.scheme.lower() == "http" and port == 80)
    ):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


def _exact_query(identifier: str) -> str:
    compact = " ".join(identifier.strip().split())
    if not compact:
        raise ValueError("public search identifier is empty")
    escaped = compact.replace('"', "")[: _MAX_QUERY_CHARS - 2]
    return f'"{escaped}"'


def _decode_results(payload: object) -> tuple[PublicSearchResult, ...]:
    if not isinstance(payload, dict):
        raise RuntimeError("Public search returned an invalid response shape.")
    web = payload.get("web")
    if web is None:
        return ()
    if not isinstance(web, dict):
        raise RuntimeError("Public search returned an invalid web result container.")
    rows = web.get("results")
    if rows is None:
        return ()
    if not isinstance(rows, list):
        raise RuntimeError("Public search returned an invalid result list.")

    results: list[PublicSearchResult] = []
    seen: set[str] = set()
    for row in rows[:_MAX_RESULTS]:
        if not isinstance(row, dict):
            continue
        url = _canonical_public_result_url(row.get("url"))
        if url is None or url in seen:
            continue
        seen.add(url)
        results.append(
            PublicSearchResult(
                title=_bounded_text(row.get("title"), limit=200),
                url=url,
                description=_bounded_text(row.get("description"), limit=_RESULT_TEXT_CHARS),
            )
        )
    return tuple(results)


async def search_exact_public_mentions(identifier: str) -> tuple[PublicSearchResult, ...]:
    """Run the existing optional exact-match search through ProviderRuntime.

    The helper keeps the private-V1 callable surface for quick research and tests.
    Missing configuration remains a no-op so the default product stays zero-spend.
    Production execution itself is owned by the process-wide governed runtime.
    """

    if not public_search_configured():
        return ()

    # Lazy import avoids a module cycle: the Brave adapter reuses the bounded
    # result decoding helpers above.
    from .providers.shared_runtime import DEFAULT_BRAVE_PROVIDER, DEFAULT_PROVIDER_RUNTIME

    subject_id = uuid4()
    identifier_id = uuid4()
    request = ExecutionRequest(
        provider_name=DEFAULT_BRAVE_PROVIDER.descriptor.name,
        subject_id=subject_id,
        identifier_id=identifier_id,
        purpose=Purpose.PUBLIC_SOURCE_RESEARCH,
        consent_acknowledged=False,
    )
    result = await DEFAULT_PROVIDER_RUNTIME.execute(
        request=request,
        query=ProviderQuery(
            subject_id=subject_id,
            identifier_id=identifier_id,
            identifier_kind=IdentifierKind.USERNAME.value,
            identifier_value=identifier,
        ),
    )
    return tuple(
        PublicSearchResult(
            title=str(item.payload.get("title", "")),
            url=item.source_locator,
            description=str(item.payload.get("description", "")),
        )
        for item in result.observations
    )
