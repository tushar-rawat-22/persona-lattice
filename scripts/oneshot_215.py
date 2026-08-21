from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1))


def append_once(path: str, marker: str, block: str) -> None:
    p = Path(path)
    text = p.read_text()
    if marker in text:
        return
    p.write_text(text.rstrip() + "\n\n" + block.strip() + "\n")


# Provider: exact canonical bsky.app/profile/<handle> admission, shared execution path.
replace_once(
    "services/api/app/providers/bluesky_public.py",
    "from urllib.parse import quote, urlencode\n",
    "from urllib.parse import quote, urlencode, urlsplit\n",
)
replace_once(
    "services/api/app/providers/bluesky_public.py",
    "\n\nclass BlueskyPublicProfileProvider:\n",
    '''\n\ndef bluesky_profile_handle_from_url(value: str) -> str | None:\n    """Return the normalized handle from an exact canonical Bluesky profile URL."""\n\n    parts = urlsplit(value)\n    if (\n        parts.scheme != "https"\n        or parts.hostname is None\n        or parts.hostname.casefold() != "bsky.app"\n        or parts.username is not None\n        or parts.password is not None\n        or parts.port is not None\n        or parts.query\n        or parts.fragment\n    ):\n        return None\n    segments = [segment for segment in parts.path.split("/") if segment]\n    if len(segments) != 2 or segments[0] != "profile":\n        return None\n    raw_handle = segments[1]\n    if parts.path not in {f"/profile/{raw_handle}", f"/profile/{raw_handle}/"} or "%" in raw_handle:\n        return None\n    if raw_handle.startswith("did:"):\n        return None\n    try:\n        handle = normalize_bluesky_handle(raw_handle)\n    except BlueskyAdmissionError:\n        return None\n    if raw_handle != handle:\n        return None\n    return handle\n\n\nclass BlueskyPublicProfileProvider:\n''',
)
replace_once(
    "services/api/app/providers/bluesky_public.py",
    '''        if query.identifier_kind != "username":\n            raise ProviderValidationError("Bluesky public profile lookup only accepts reviewed handles.")\n        try:\n            handle = normalize_bluesky_handle(query.identifier_value)\n        except BlueskyAdmissionError as exc:\n            raise ProviderValidationError(str(exc)) from exc\n\n        payload = await self.fetcher(handle)\n''',
    '''        if query.identifier_kind == "username":\n            try:\n                handle = normalize_bluesky_handle(query.identifier_value)\n            except BlueskyAdmissionError as exc:\n                raise ProviderValidationError(str(exc)) from exc\n        elif query.identifier_kind == "url":\n            handle = bluesky_profile_handle_from_url(query.identifier_value)\n            if handle is None:\n                raise ProviderValidationError(\n                    "Bluesky URL lookup requires an exact canonical handle profile URL."\n                )\n        else:\n            raise ProviderValidationError(\n                "Bluesky public profile lookup only accepts reviewed handles or exact handle profile URLs."\n            )\n\n        payload = await self.fetcher(handle)\n''',
)

# Registry/catalog/binding: extend one existing governed source; no new quota/runtime owner.
replace_once(
    "services/api/app/providers/registry.py",
    '''        reason=(\n            "Official unauthenticated Bluesky public AppView profile lookup for valid AT handles; "\n            "minimal public fields only, with public-web opt-out and unavailable accounts neutral."\n        ),\n        version="app.bsky.actor.getProfile",\n        source_category=SourceCategory.PUBLIC_WEB,\n        allowed_purposes=SAFE_PURPOSES,\n        supported_identifier_kinds=USERNAME_ONLY,\n''',
    '''        reason=(\n            "Official unauthenticated Bluesky public AppView profile lookup for valid AT handles or exact "\n            "canonical bsky.app handle profile URLs; minimal public fields only, with public-web opt-out "\n            "and unavailable accounts neutral."\n        ),\n        version="app.bsky.actor.getProfile",\n        source_category=SourceCategory.PUBLIC_WEB,\n        allowed_purposes=SAFE_PURPOSES,\n        supported_identifier_kinds=USERNAME_URL,\n''',
)
replace_once(
    "services/api/app/intelligence/source_catalog.py",
    '''    SourceCapability(\n        name="bluesky_public_profile",\n        accepts=frozenset({LeadKind.USERNAME}),\n''',
    '''    SourceCapability(\n        name="bluesky_public_profile",\n        accepts=frozenset({LeadKind.USERNAME, LeadKind.URL}),\n''',
)
replace_once(
    "services/api/app/intelligence/source_catalog.py",
    '''        note=(\n            "Unauthenticated public AppView profile lookup for syntactically valid AT handles only; "\n            "public-web opt-out and unavailable-account states are neutral completed outcomes."\n        ),\n''',
    '''        note=(\n            "Unauthenticated public AppView profile lookup for valid AT handles or exact canonical "\n            "bsky.app handle profile URLs; public-web opt-out and unavailable-account states are neutral."\n        ),\n''',
)
replace_once(
    "services/api/app/intelligence/source_bindings.py",
    '''    SourceBinding(\n        source_name="bluesky_public_profile",\n        backend=SourceExecutionBackend.M3_GOVERNED_ADAPTER,\n        provider_name="bluesky_public_profile",\n        accepts=frozenset({LeadKind.USERNAME}),\n        migration_note=(\n            "Valid AT handles execute through the shared ProviderRuntime; ordinary usernames are "\n            "filtered as not applicable before provider execution."\n        ),\n    ),\n''',
    '''    SourceBinding(\n        source_name="bluesky_public_profile",\n        backend=SourceExecutionBackend.M3_GOVERNED_ADAPTER,\n        provider_name="bluesky_public_profile",\n        accepts=frozenset({LeadKind.USERNAME, LeadKind.URL}),\n        migration_note=(\n            "Valid AT handles and exact canonical bsky.app handle profile URLs execute through one shared "\n            "ProviderRuntime adapter and provider budget; non-applicable values stop before execution."\n        ),\n    ),\n''',
)

# Research: add URL applicability helper, URL execution wrapper and one URL routing block.
replace_once(
    "services/api/app/research.py",
    "from .providers.bluesky_admission import BlueskyAdmissionError, normalize_bluesky_handle\n",
    "from .providers.bluesky_admission import BlueskyAdmissionError, normalize_bluesky_handle\nfrom .providers.bluesky_public import bluesky_profile_handle_from_url\n",
)
replace_once(
    "services/api/app/research.py",
    '''    return [_bluesky_observation_from_provider(item) for item in result.observations]\n\n\nasync def _dns_observations(\n''',
    '''    return [_bluesky_observation_from_provider(item) for item in result.observations]\n\n\nasync def _bluesky_url_observations(\n    normalized_value: str,\n    *,\n    subject_id,\n    identifier_id,\n    purpose: Purpose,\n    consent_acknowledged: bool,\n) -> list[QuickObservation]:\n    request = ExecutionRequest(\n        provider_name=DEFAULT_BLUESKY_PROVIDER.descriptor.name,\n        subject_id=subject_id,\n        identifier_id=identifier_id,\n        purpose=purpose,\n        consent_acknowledged=consent_acknowledged,\n    )\n    result = await DEFAULT_PROVIDER_RUNTIME.execute(\n        request=request,\n        query=ProviderQuery(\n            subject_id=subject_id,\n            identifier_id=identifier_id,\n            identifier_kind=IdentifierKind.URL.value,\n            identifier_value=normalized_value,\n        ),\n    )\n    return [_bluesky_observation_from_provider(item) for item in result.observations]\n\n\nasync def _dns_observations(\n''',
)
replace_once(
    "services/api/app/research.py",
    '''        observations.extend(gitlab_url_observations)\n\n    if stack_overflow_user_id_from_url(normalized_value) is not None:\n''',
    '''        observations.extend(gitlab_url_observations)\n\n    if bluesky_profile_handle_from_url(normalized_value) is not None:\n        try:\n            bluesky_url_observations = await _bluesky_url_observations(\n                normalized_value,\n                subject_id=subject_id,\n                identifier_id=identifier_id,\n                purpose=purpose,\n                consent_acknowledged=consent_acknowledged,\n            )\n        except Exception as exc:\n            bluesky_url_observations = []\n            source_run = _source_run_for_exception(\n                source_name="bluesky_public_profile",\n                lead_kind=LeadKind.URL,\n                exc=exc,\n            )\n            if source_run is not None:\n                source_runs.append(source_run)\n            if source_run is None or source_run.state not in {\n                SourceRunState.WITHHELD,\n                SourceRunState.NOT_FOUND,\n            }:\n                warnings.append("Bluesky exact public-profile metadata was temporarily unavailable.")\n        else:\n            source_runs.append(\n                source_result_record(\n                    source_name="bluesky_public_profile",\n                    lead_kind=LeadKind.URL,\n                    observation_count=len(bluesky_url_observations),\n                )\n            )\n        observations.extend(bluesky_url_observations)\n\n    if stack_overflow_user_id_from_url(normalized_value) is not None:\n''',
)

# Direct provider + URL quick-research regression coverage.
Path("services/api/tests/test_bluesky_profile_urls.py").write_text('''# SPDX-License-Identifier: Apache-2.0\nfrom __future__ import annotations\n\nimport pytest\n\nimport app.research as research_module\nfrom app.intelligence.contracts import LeadKind\nfrom app.intelligence.source_bindings import SOURCE_BINDING_BY_NAME\nfrom app.intelligence.source_catalog import SOURCE_BY_NAME\nfrom app.intelligence.source_states import SourceRunReason, SourceRunState\nfrom app.models import Purpose\nfrom app.providers import ProviderObservationData, ProviderQuery, ProviderResult, ProviderRuntime\nfrom app.providers.bluesky_public import BlueskyPublicProfileProvider, bluesky_profile_handle_from_url\nfrom app.providers.errors import ProviderValidationError\nfrom app.providers.registry import PROVIDER_BY_NAME\nfrom app.research import ResearchKind, run_quick_research\n\n\ndef test_exact_bluesky_handle_profile_url_admission_is_fail_closed() -> None:\n    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.bsky.social") == "alice.bsky.social"\n    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.bsky.social/") == "alice.bsky.social"\n    assert bluesky_profile_handle_from_url("https://bsky.app/profile/Alice.Bsky.Social") is None\n    assert bluesky_profile_handle_from_url("https://bsky.app/profile/did:plc:abc") is None\n    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.bsky.social/post/3abc") is None\n    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice%2Ebsky.social") is None\n    assert bluesky_profile_handle_from_url("http://bsky.app/profile/alice.bsky.social") is None\n    assert bluesky_profile_handle_from_url("https://user@bsky.app/profile/alice.bsky.social") is None\n    assert bluesky_profile_handle_from_url("https://bsky.app:443/profile/alice.bsky.social") is None\n    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.bsky.social?x=1") is None\n    assert bluesky_profile_handle_from_url("https://bsky.app/profile/alice.test") is None\n\n\n@pytest.mark.asyncio\nasync def test_provider_reuses_handle_lookup_for_exact_profile_url() -> None:\n    seen: list[str] = []\n\n    async def fetcher(handle: str):\n        seen.append(handle)\n        return {\n            "did": "did:plc:alice",\n            "handle": "alice.bsky.social",\n            "displayName": "Alice",\n        }\n\n    provider = BlueskyPublicProfileProvider(fetcher=fetcher)\n    result = await provider.execute(\n        ProviderQuery(\n            identifier_kind="url",\n            identifier_value="https://bsky.app/profile/alice.bsky.social",\n        ),\n        None,\n    )\n    assert seen == ["alice.bsky.social"]\n    assert len(result.observations) == 1\n    assert result.observations[0].source_locator == "https://bsky.app/profile/alice.bsky.social"\n    assert result.observations[0].payload["identity_claim"] is False\n\n\n@pytest.mark.asyncio\nasync def test_provider_rejects_did_and_post_urls_without_fetch() -> None:\n    async def unexpected(_handle: str):\n        raise AssertionError("provider must not fetch non-applicable Bluesky URL")\n\n    provider = BlueskyPublicProfileProvider(fetcher=unexpected)\n    for value in (\n        "https://bsky.app/profile/did:plc:abc",\n        "https://bsky.app/profile/alice.bsky.social/post/3abc",\n    ):\n        with pytest.raises(ProviderValidationError):\n            await provider.execute(ProviderQuery(identifier_kind="url", identifier_value=value), None)\n\n\ndef test_catalog_binding_and_descriptor_share_username_url_contract() -> None:\n    assert SOURCE_BY_NAME["bluesky_public_profile"].accepts == frozenset({LeadKind.USERNAME, LeadKind.URL})\n    assert SOURCE_BINDING_BY_NAME["bluesky_public_profile"].accepts == frozenset({LeadKind.USERNAME, LeadKind.URL})\n    assert PROVIDER_BY_NAME["bluesky_public_profile"].supported_identifier_kinds == frozenset({"username", "url"})\n    descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]\n    assert descriptor.rate_limit == 30\n    assert descriptor.rate_window_seconds == 60.0\n\n\n@pytest.mark.asyncio\nasync def test_exact_profile_url_runs_bluesky_once_through_shared_runtime(monkeypatch) -> None:\n    class FakeBlueskyProvider:\n        descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]\n\n        def __init__(self) -> None:\n            self.queries = []\n\n        async def execute(self, query, secret):\n            self.queries.append(query)\n            return ProviderResult(\n                observations=(\n                    ProviderObservationData(\n                        source_locator="https://bsky.app/profile/alice.bsky.social",\n                        payload={\n                            "did": "did:plc:alice",\n                            "handle": "alice.bsky.social",\n                            "display_name": "Alice",\n                            "account_candidate": True,\n                            "identity_claim": False,\n                            "field_visibility": "public_profile_api",\n                            "public_web_visibility": "allowed",\n                        },\n                    ),\n                )\n            )\n\n    async def no_dns(*args, **kwargs):\n        return []\n\n    async def no_wayback(*args, **kwargs):\n        return []\n\n    async def no_search(_value: str):\n        return ()\n\n    provider = FakeBlueskyProvider()\n    runtime = ProviderRuntime(adapters=[provider])\n    monkeypatch.setattr(research_module, "DEFAULT_BLUESKY_PROVIDER", provider)\n    monkeypatch.setattr(research_module, "DEFAULT_PROVIDER_RUNTIME", runtime)\n    monkeypatch.setattr(research_module, "_dns_observations", no_dns)\n    monkeypatch.setattr(research_module, "_wayback_observations", no_wayback)\n\n    report = await run_quick_research(\n        kind=ResearchKind.URL,\n        value="https://bsky.app/profile/alice.bsky.social",\n        purpose=Purpose.SELF_AUDIT,\n        consent_acknowledged=True,\n        public_search_lookup=no_search,\n    )\n\n    assert len(provider.queries) == 1\n    assert provider.queries[0].identifier_kind == "url"\n    assert provider.queries[0].identifier_value == "https://bsky.app/profile/alice.bsky.social"\n    observations = [item for item in report.observations if item.source == "bluesky_public_profile"]\n    assert len(observations) == 1\n    source_run = next(item for item in report.source_runs if item.source_name == "bluesky_public_profile")\n    assert source_run.state is SourceRunState.EXECUTED\n    assert source_run.reason is SourceRunReason.RESULTS_RETURNED\n    assert source_run.observation_count == 1\n''')

# Update stale architecture assertions where they encode the previous username-only contract.
for test_path in Path("services/api/tests").glob("test_*.py"):
    text = test_path.read_text()
    updated = text.replace(
        'PROVIDER_BY_NAME["bluesky_public_profile"].supported_identifier_kinds == frozenset({"username"})',
        'PROVIDER_BY_NAME["bluesky_public_profile"].supported_identifier_kinds == frozenset({"username", "url"})',
    )
    updated = updated.replace(
        'SOURCE_BY_NAME["bluesky_public_profile"].accepts == frozenset({LeadKind.USERNAME})',
        'SOURCE_BY_NAME["bluesky_public_profile"].accepts == frozenset({LeadKind.USERNAME, LeadKind.URL})',
    )
    if updated != text:
        test_path.write_text(updated)

# Human-maintainer documentation. Keep additions factual and bounded.
Path("docs/source-admissions/BLUESKY_EXACT_PROFILE_URL.md").write_text('''# Bluesky exact profile URL admission\n\nReviewed: 2026-08-21\n\nPersonaLattice may use an explicit canonical `https://bsky.app/profile/<handle>` URL as another entry point to the already-active Bluesky public-profile source. The URL does not authorize broader Bluesky collection.\n\nThe adapter accepts only HTTPS `bsky.app` URLs with exactly `profile` plus one canonical handle segment. DID profile URLs, post URLs, encoded handles, credentials, custom ports, queries and fragments are rejected before provider execution. The handle still passes the existing AT-handle normalizer and reserved/non-public TLD checks.\n\nExecution reuses the official unauthenticated `app.bsky.actor.getProfile` lookup and the existing process-owned 30 requests/minute budget shared with username research. The retained fields remain DID, normalized handle, optional bounded display name, public-web/account-candidate state and `identity_claim=false`. Posts, graphs, feeds, activity and contact data are not requested.\n\nPublic-web opt-out and unavailable-account behavior is unchanged. This extension adds no new lead-promotion rule and no second provider or quota bucket.\n''')
append_once(
    "THIRD_PARTY.md",
    "Bluesky exact profile URL extension (2026-08-21)",
    '''### Bluesky exact profile URL extension (2026-08-21)\n\nThe existing credentialless Bluesky public-profile source also accepts an explicit canonical `https://bsky.app/profile/<handle>` URL. It reuses the same public AppView lookup, reviewed retained fields and 30/minute process budget. DID profile URLs, posts and broader profile/activity expansion are outside this admission. See `docs/source-admissions/BLUESKY_EXACT_PROFILE_URL.md`.''',
)
append_once(
    "docs/SOURCE_ADMISSION_QUEUE.md",
    "Bluesky exact profile URLs — admitted 2026-08-21",
    '''## Bluesky exact profile URLs — admitted 2026-08-21\n\nExact canonical handle profile URLs reuse `bluesky_public_profile`; no new provider or quota pool was added. DID/post URLs remain outside scope. The source retains the existing minimal public profile fields and existing neutral opt-out/unavailable semantics.''',
)
append_once(
    "docs/ROADMAP.md",
    "Bluesky exact profile URL reachability (2026-08-21)",
    '''### Bluesky exact profile URL reachability (2026-08-21)\n\nThe active Bluesky source accepts exact canonical `bsky.app/profile/<handle>` URLs in addition to handle seeds. URL and handle research share one 30/minute governed runtime budget and the same minimal retained profile contract. DID/post URLs remain out of scope.''',
)
append_once(
    "docs/CONTINUITY.md",
    "Bluesky exact profile URL package — Issue #215",
    '''## Bluesky exact profile URL package — Issue #215\n\nThis package extends the existing `bluesky_public_profile` source from username handles to exact canonical `https://bsky.app/profile/<handle>` URLs. It reuses one process-owned adapter and the existing 30/minute budget. DID/post URLs and noncanonical handles stop before execution; existing public-web opt-out, account-unavailable, no-match and retained-field semantics are unchanged. No recursion or M5 policy changed.\n\nMerge SHA and exact-head CI are recorded after the PR is verified and merged.''',
)

print("oneshot 215 patch complete")
