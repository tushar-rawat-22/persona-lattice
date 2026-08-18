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
- Verified main after PR #81: `17f2e0f6c79749d5965b819267bb46650fa211ca`
- PR #81 exact final tested head: `148ca56fc641703ec53615aa59b8efd66186b1e1`
- PR #81 final CI: run `32150116712`, success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and deployment image
- PR #81 decision: ADR 0046, private UI canonical-reference resolution
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #81 closes the temporary response-hydration seam left after PRs #77/#79. New retained reports already used canonical references; the API had been rebuilding copied connected-field values and edge source locators solely because the admin UI expected the old display shape. The browser now resolves those references directly, and `CaseStore` returns the retained report JSON unchanged.

Quick connected-field resolution uses `observation_index + detail_field` and checks the reviewed kind/field mapping plus canonical observation provenance. Converged edge resolution uses `lead_decision_index -> source_observation_index`, verifies an admitted decision, parent/child/reason agreement, exactly one parent node, source-field presence and canonical observation provenance. Mixed legacy/reference shapes or unprovable references are not synthesized; the UI displays an unavailable-reference message.

Historical retained cases created before ADRs 0044/0045 remain readable through explicit read-only browser compatibility branches for their original self-contained fields. There is no database migration or compatibility write-back.

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

The baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Brave remains optional/metered; no `BRAVE_SEARCH_API_KEY` means no Brave attempt.

Uploaded content is untrusted data. Extraction is never execution authority. A candidate becomes executable only after explicit human review/authorization, and only a separate explicit run action may start research.

## Stable architecture

- Next.js private/public UI: `apps/web`
- FastAPI API: `services/api`
- evidence/persistence/normalization: `services/api/app/evidence`
- bounded file intake + review: `services/api/app/uploads`
- upload-review HTTP boundary: `services/api/app/upload_review_api.py`
- reviewed-candidate case execution: `services/api/app/uploads/research_service.py`
- governed provider execution: `services/api/app/providers`
- deterministic correlation: `services/api/app/correlation`
- convergence: `services/api/app/convergence.py`
- retained converged reference validation: `services/api/app/converged_report.py`
- typed leads/frontier/source planning/reporting/evaluation: `services/api/app/intelligence`
- quick structured-report references: `services/api/app/reporting.py`
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

Document-intake/review backend checkpoints:

- PR #56: deterministic candidate character spans and fail-closed reviewed identifier promotion;
- PR #58: extraction-time PDF page spans and corrected flattened-text limits;
- PR #60: short-lived server-owned candidate review state without raw-document retention;
- PR #62/#63: atomic confirm/reject/re-review/promotion with immutable candidate value/provenance;
- PR #64: authenticated + CSRF-protected HTTP review actions;
- PR #66: separate explicit retained-case execution from a currently confirmed, research-authorized server-owned candidate.

Architecture/privacy closure checkpoints:

- PR #68: catalog/binding/registry/shared-runtime ownership and zero-spend invariants; ADR 0040;
- PR #70: convergence requires canonical typed source-run reports; ADR 0041;
- PR #72: complete quick-provider payloads have one retained owner; ADR 0042;
- PR #74: M5 candidate provenance references canonical node observations; ADR 0043;
- PR #77: converged pivot provenance uses canonical observation/decision references; ADR 0044;
- PR #79: quick connected fields use canonical observation references; ADR 0045;
- PR #81: private UI resolves those canonical quick/converged references and API response hydration is removed; ADR 0046.

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

The canonical retained-report display contract is closed: new quick connected fields and converged edges are resolved in the private browser from retained references, while historical self-contained cases remain readable without server hydration.

The next bounded V2-D block is operator workflow visibility. Expose the already-built reviewed-document state/actions, explicit start-case control, retained seed provenance and typed source-state/evaluation summaries without re-deriving authorization, provider policy or evidence semantics in the browser.

After that, run a final architecture/compatibility/documentation/zero-spend consistency audit and explicitly record V2-D closure if no material gap remains. Do not activate new third-party providers before that closure.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
