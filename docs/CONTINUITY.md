# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only
- Verified implementation main after PR #64: `89969e3747ebe1a9cd6f12274738cae1123ec629`
- PR #64 exact tested head: `8fb664bc31ae09a4b506ae308744e88e17412a7e`
- PR #64 CI run: `32103737982`, success across API 3.11/3.13, dependency audits, Ruff, web and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #64 closes the private HTTP boundary for document review. Confirm, reject, reopen and promote are exposed under `/v1/files/review/{artifact_id}/{candidate_id}` and all use the existing authenticated write/CSRF boundary. Requests carry only artifact and candidate UUIDs; value, identifier kind, review authorization and provenance are reloaded from server-owned SQLite state.

Review-state responses deliberately omit the candidate value. Promotion returns the typed reviewed lead with its normalized value and `artifact://` provenance locator, but it does not schedule or execute provider research. Successful review actions emit bounded audit metadata without identifier values, artifact/candidate IDs, source locators or document text. ADR 0038 records the boundary.

CI exposed one stale test assumption: `test_m6_keeps_no_browser_facing_dashboard_http_endpoint` assumed every `app.routes` item had a `.path`. FastAPI router inclusion introduced an internal non-path entry. The test was narrowed to path-bearing routes only; runtime behavior was not changed to satisfy the brittle assertion. An intermediate over-broad test-file edit was caught before merge and restored; the final diff changes that test by one line only.

## Permanent evidence semantics

- Observations, factual Claims and correlation results remain separate.
- Every factual conclusion keeps provenance.
- A discovered clue is a research lead, not proof of identity.
- Same-handle reuse alone is weak evidence.
- M5 is deterministic evidence-strength triage, not identity probability.
- `calibration_status=uncalibrated` and `is_identity_claim=false` remain fixed.
- Contradictions/vetoes and stale evidence remain visible.
- Unknown, not-found, unavailable, blocked and budget-stopped remain distinct outcomes.
- No AI/ML/embedding/biometric identity decision is in the correlation path.

## Permanent security, privacy and cost boundary

Allowed scope is attributable public information and explicitly authorized data. PersonaLattice does not add private-account bypass, login/account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

The baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Missing optional configuration must degrade explicitly rather than breaking baseline research.

Brave remains optional/metered. No `BRAVE_SEARCH_API_KEY` means no Brave attempt. Do not make it mandatory or expand its query scope during architecture closure.

Uploaded content is untrusted data. Extraction is never execution authority. A candidate enters the executable lead path only after explicit human review/authorization, and only for supported identifier kinds.

## Stable architecture

- Next.js UI: `apps/web`
- FastAPI API: `services/api`
- evidence/persistence/normalization: `services/api/app/evidence`
- bounded file intake + review: `services/api/app/uploads`
- upload-review HTTP boundary: `services/api/app/upload_review_api.py`
- governed provider execution: `services/api/app/providers`
- deterministic correlation: `services/api/app/correlation`
- convergence: `services/api/app/convergence.py`
- typed leads/frontier/source planning/reporting/evaluation: `services/api/app/intelligence`
- quick research: `services/api/app/research.py`
- retained cases: `services/api/app/cases.py`
- source expansion design: `docs/V2_SOURCE_EXPANSION_PLAN.md`

M0-M6 are complete. Private V1 one-admin research, retention/deletion, audit, local HTTPS-tunnel acceptance and the ephemeral canonical evidence graph are implemented.

## V2 checkpoint

### V2-A — typed lead graph — complete

PR #20. Exact-field lead extraction, M1-consistent normalization, typed dispositions and blocked sensitive field classes.

### V2-B — deterministic frontier — complete

PR #21. Reservation-safe frontier, duplicate/cycle suppression, reason-coded outcomes and bounded lead-graph report state. Production limits remain depth 2 / 12 nodes.

### V2-C — capability registry/planner — complete

PR #22. Capability, lifecycle/cost/configuration/review state and zero-spend planning are separated from execution authority.

### V2-D — runtime consistency and architecture closure — active

Current network execution ownership:

- Sherlock — governed runtime
- GitHub — governed runtime
- GitLab — governed runtime
- Codeforces — governed runtime
- public DNS — governed runtime
- optional Brave exact-match search — governed runtime
- executable legacy network allowance — **empty**

Key provider/runtime PRs: #24-#32, #50, #52, #54.

Key source-state/report/evaluation PRs: #34-#48. These establish typed source states/reasons, privacy-bounded projections, factual quick-research population, deterministic per-source counters, full-vocabulary fixture coverage, graph-growth/duplicate counters, label-gated wrong-pivot measurement and network-free graph-limit comparison through the real frontier scheduler.

Document-intake checkpoints:

- PR #56: deterministic candidate character spans plus fail-closed reviewed identifier promotion contract;
- PR #58: extraction-time PDF page spans, exact page attribution and corrected flattened-text bounds;
- PR #60: short-lived server-owned candidate review persistence without raw document retention;
- PR #62/#63: atomic server-owned confirm/reject/re-review/promotion service with immutable candidate value/provenance and a hardened generic update seam;
- PR #64: authenticated + CSRF-protected HTTP confirm/reject/reopen/promote actions over the server-owned review record.

The document-review backend now reaches a typed promoted lead without trusting browser-supplied candidate data. It intentionally stops before provider execution.

## Source-run semantics

Retained source-run records carry logical source name, lead kind, state/reason, observation count and execution/terminal flags. They do not duplicate identifier values, source locators, provider payloads, secrets or exception text.

Critical distinctions:

- completed call with results → `executed / results_returned`;
- completed call with zero results → `not_found / no_match`;
- optional source absent → `unavailable / optional_not_configured`, no attempt;
- local budget stop → `budget_stopped / local_budget`, no provider contact;
- provider-policy rejection → blocked, no attempt;
- required server-side secret absent → unavailable, no attempt;
- remote rate limit / proven execution failure → unavailable, attempted;
- returned malformed result → unavailable, attempted only when post-attempt phase is mechanically proven;
- generic `ProviderValidationError` → no source-run record because its phase is ambiguous.

`source_provider_exception_record()` is the governed provider-exception mapping authority. Warnings are human context only and are never parsed into source state.

## Document candidate semantics

- file preview remains review-only and temp files are deleted after bounded extraction;
- successful preview persists only short-lived candidate review metadata, not uploaded file bytes or complete extracted text;
- candidate review state defaults to 24-hour retention and expires independently of retained research cases;
- server lookup and mutation require both artifact ID and candidate ID;
- stored payload IDs are revalidated against SQLite row keys;
- atomic review mutation may change only review status and external-research authorization;
- candidate value, kind, IDs, origin, type and page/character provenance are immutable during review mutation;
- confirm authorizes supported identifier candidates; reject/re-review revoke authorization;
- HTTP mutation requests carry only artifact/candidate UUIDs and use `require_admin_write`;
- review-state responses omit the candidate value;
- promotion reloads current server-owned state, returns a typed reviewed lead and does not automatically call a provider;
- PDF candidate page attribution is mechanically derived from extraction-time page spans;
- claims and unsupported identifier kinds remain non-executable;
- names/organizations are not silently upgraded to executable research seeds.

## Graph-evaluation semantics

Graph evaluation records growth, maximum depth, admitted pivots, duplicate suppression, provider failures and budget stops. Wrong-pivot truth requires explicit synthetic or consented relevance labels. Production pivots without labels remain unscored.

The graph-limit harness uses the real `LeadFrontier`. Its regression fixture shows that extra depth can admit both useful and wrong pivots; it is not authorization to raise production limits.

## Current deliberate limits

- convergence max depth: 2;
- convergence max nodes: 12;
- no new third-party provider activation during V2-D closure;
- planned sources remain non-executable;
- newly discovered phone leads require review;
- contextual name/organization/location remain non-autonomous;
- public-search snippets do not become automatic identifier leads;
- Brave remains optional and excluded from the zero-spend requirement;
- no identity probability or universal-account claims.

## Immediate next gate

Define the explicit backend transition from a promoted reviewed document lead into a chosen research/case run before wiring UI controls around it.

Requirements:

1. keep candidate confirmation/promotion separate from research execution; no review action may trigger provider traffic;
2. the execution action should reference server-owned artifact/candidate state rather than accept an arbitrary browser-supplied identifier as a reviewed-document authorization claim;
3. reload and revalidate current confirmed/research-authorized state immediately before constructing the research request;
4. require the existing authenticated write/CSRF boundary and normal purpose/consent enforcement;
5. preserve the promoted lead's artifact/candidate/page/character provenance in the resulting run/report without creating a second raw-document store;
6. fail closed if the short-lived review candidate expired, was reopened/rejected, or is not an executable identifier kind;
7. emit privacy-bounded audit metadata without copying identifier values;
8. remain a zero-spend local capability and do not activate any new provider/source.

After that backend transition, expose the document-review flow and existing source-state/evaluation summaries cleanly to the private operator UI, then run the final V2-D catalog/binding/runtime/report/privacy/zero-spend consistency review. Only after V2-D closure should new third-party providers be reviewed.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
