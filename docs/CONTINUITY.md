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
- Verified implementation main after PR #74: `bea58d7a6a832e10bf4304234be0b7d43efaa7c3`
- PR #74 exact tested head: `8e8a2b4686e80d2d4c69d7e47d416ce0c2d2ecdd`
- PR #74 CI run: `32127790638`, success across API 3.11/3.13, dependency audits, Ruff, web lint/typecheck/build and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #74 closes a retained converged-M5 provenance duplication gap. Canonical converged node observations remain the retained owner of complete provider source/locator/details. New live-M5 evaluation records no longer copy `candidate_source` or `candidate_source_locator`; they reference the canonical observation by `candidate_node` plus zero-based `candidate_observation_index`. ADR 0043 records the decision.

A cross-layer review caught a compatibility defect before merge: the private admin UI still consumed the removed M5 fields. The UI now resolves new M5 evaluations through the canonical node observation. It retains read-only support for older retained cases that still contain the legacy M5 source/source-locator fields, so historical case JSON does not need migration or rewriting.

Regression coverage proves an arbitrary provider detail and candidate locator occur only once in a new retained converged payload while M5 score/outcome semantics remain unchanged.

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

Key source-state/report/evaluation PRs: #34-#48 and #70. These establish typed source states/reasons, privacy-bounded projections, factual quick-research population, deterministic per-source counters, full-vocabulary fixture coverage, graph-growth/duplicate counters, label-gated wrong-pivot measurement, network-free graph-limit comparison through the real frontier scheduler, and a fail-closed convergence contract for typed source-run state.

Document-intake/review checkpoints:

- PR #56: deterministic candidate character spans plus fail-closed reviewed identifier promotion contract;
- PR #58: extraction-time PDF page spans, exact page attribution and corrected flattened-text bounds;
- PR #60: short-lived server-owned candidate review persistence without raw document retention;
- PR #62/#63: atomic server-owned confirm/reject/re-review/promotion service with immutable candidate value/provenance and a hardened generic update seam;
- PR #64: authenticated + CSRF-protected HTTP confirm/reject/reopen/promote actions;
- PR #66: separate authenticated retained-case execution from a currently confirmed, research-authorized server-owned candidate.

Architecture/privacy consistency checkpoints:

- PR #68: cross-layer catalog/binding/registry/shared-runtime ownership and zero-spend invariants; ADR 0040;
- PR #70: convergence requires canonical typed source-run reports and no longer infers a missing contract as an empty report; ADR 0041;
- PR #72: complete quick-provider payloads have one retained owner; structured quick-report copies are removed; ADR 0042;
- PR #74: converged M5 candidate provenance references canonical node observations instead of copying source/locator fields; ADR 0043.

The document-review backend reaches a retained quick or converged case without trusting browser-supplied candidate data and without making review actions trigger provider execution.

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

The private operator UI remains the next product-facing block: wire document review/run state, explicit provider-start controls, retained seed provenance and existing source-state/evaluation summaries without re-deriving backend semantics in the browser.

For backend architecture closure, quick full-payload duplication and converged M5 candidate-provenance duplication are closed after PRs #72 and #74. Next inspect converged node/edge/lead-decision provenance ownership. Do not remove edge or lead provenance merely because values repeat: those records may need their own source to explain traversal or non-executed decisions. Remove only duplication with no independent explanatory owner. After that, decide whether the bounded quick connected-field value/source-locator projection remains an intentional operator index or moves to canonical-observation references.

Do not activate new third-party providers until V2-D closure is explicitly recorded.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
