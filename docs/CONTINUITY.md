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
- Verified implementation main after PR #66: `58c582b1db7ef62254ea8bcabc732ed0514c567d`
- PR #66 exact tested head: `7d51fb28e331de9c388e0dc1ab393f281d5b685b`
- PR #66 CI run: `32107499455`, success across API 3.11/3.13, dependency audits, Ruff, web and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #66 closes the backend transition from reviewed upload evidence into an explicit retained research case. The new `/v1/files/review/{artifact_id}/{candidate_id}/run-case` action uses the existing authenticated write/CSRF boundary, accepts only mode/purpose/consent in the body, reloads the current server-owned candidate immediately before execution and reuses the existing promotion contract. Browser-supplied identifier values or provenance never become reviewed-document authorization state.

Purpose/consent is enforced before provider execution. Pending, rejected, reopened, expired, mismatched or unsupported candidates fail closed. Confirmation and promotion remain non-executing state transitions; provider traffic begins only through the separate `run-case` action.

Retained quick and converged cases now carry bounded `seed_provenance` for reviewed-document seeds. It stores only the existing `reviewed_upload_candidate` source and `artifact://` locator, which contains artifact/candidate identity plus mechanically derived page/character location when available. It does not retain file bytes, surrounding extracted prose or complete extracted text. The HTTP response returns case metadata without echoing the identifier value. Audit metadata records case ID, mode and seed kind only. ADR 0039 records this boundary.

Two implementation ideas were rejected during review before merge. First, creating a quick case and then deleting/recreating it merely to attach provenance would have introduced a transient retained record and broken single-write semantics. Second, a generic report-extension hook was broader than this block required and would have created a future schema escape hatch. The final implementation uses one write and one dedicated optional `seed_provenance` field.

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
- reviewed-candidate case execution: `services/api/app/uploads/research_service.py`
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

Document-intake/review checkpoints:

- PR #56: deterministic candidate character spans plus fail-closed reviewed identifier promotion contract;
- PR #58: extraction-time PDF page spans, exact page attribution and corrected flattened-text bounds;
- PR #60: short-lived server-owned candidate review persistence without raw document retention;
- PR #62/#63: atomic server-owned confirm/reject/re-review/promotion service with immutable candidate value/provenance and a hardened generic update seam;
- PR #64: authenticated + CSRF-protected HTTP confirm/reject/reopen/promote actions;
- PR #66: separate authenticated retained-case execution from a currently confirmed, research-authorized server-owned candidate.

The document-review backend now reaches a retained quick or converged case without trusting browser-supplied candidate data and without making review actions trigger provider execution.

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
- HTTP review and execution routes use `require_admin_write`;
- review-state responses omit the candidate value;
- promotion reloads current server-owned state, returns a typed reviewed lead and does not call providers;
- `run-case` reloads that same current state immediately before execution and does not accept an identifier value in the request body;
- blocked purpose or missing required consent stops before provider execution;
- retained reviewed-document cases carry bounded `seed_provenance` using the existing `artifact://` locator;
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

Wire the document review/run workflow and existing source-state/evaluation summaries into the private operator UI.

Requirements:

1. keep confirm/promote and `run-case` visually and behaviorally distinct;
2. make it explicit that provider traffic begins only when the operator starts the case;
3. do not present a promoted lead as proof of identity;
4. show review state and page/character provenance without duplicating unnecessary document content;
5. surface source execution states and evaluation summaries from the existing backend contracts rather than re-deriving them in the browser;
6. keep the same authenticated private boundary and zero-spend local operation.

After the operator workflow is usable, run the final V2-D catalog/binding/runtime/report/privacy/zero-spend consistency review. Only after V2-D closure should new third-party providers be reviewed.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
