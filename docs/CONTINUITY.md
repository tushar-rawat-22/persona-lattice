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
- Verified main after PR #87: `f859c99083a87504357fcaa000dbfff2e35af443`
- PR #87 exact tested head: `3c2d35761c29eed0e7e506205eaf800dd3edeba1`
- PR #87 CI: run `32166209900`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and deployment image
- PR #87 decision: ADR 0049, private case views consume retained reviewed-upload provenance and typed source state/evaluation directly
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #87 closes the private operator visibility gap left after PR #85. Quick retained cases show their top-level `source_runs` projection; converged cases show the same projection per research node; reviewed-upload cases show retained `seed_provenance`. Historical cases that predate typed source-run retention show source execution state as unavailable instead of receiving guessed backfill. The case UI reads retained state, reason, attempt flags and counters directly; it does not parse warnings or reconstruct provider policy in TypeScript.

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

Uploaded content is untrusted data. Extraction is never execution authority. A candidate becomes externally research-authorized only after explicit human confirmation, and only a separate explicit run action may start research.

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
- private case view: `apps/web/app/admin/quick-research.tsx`
- private upload-review UI: `apps/web/app/admin/upload-review-workflow.tsx`
- source expansion design: `docs/V2_SOURCE_EXPANSION_PLAN.md`

M0-M6 are complete. Private V1 one-admin research, retention/deletion, audit, local HTTPS-tunnel acceptance and the ephemeral canonical evidence graph are implemented.

## V2 checkpoint

### V2-A — typed lead graph — complete

PR #20. Exact-field lead extraction, M1-consistent normalization, typed dispositions and blocked sensitive field classes.

### V2-B — deterministic frontier — complete

PR #21. Reservation-safe frontier, duplicate/cycle suppression, reason-coded outcomes and bounded lead-graph report state. Production limits remain depth 2 / 12 nodes.

### V2-C — capability registry/planner — complete

PR #22. Capability, lifecycle/cost/configuration/review state and zero-spend planning are separated from execution authority.

### V2-D — runtime consistency and architecture closure — final audit next

Current network execution ownership:

- Sherlock — governed runtime
- GitHub — governed runtime
- GitLab — governed runtime
- Codeforces — governed runtime
- public DNS — governed runtime
- optional Brave exact-match search — governed runtime
- executable legacy network allowance — **empty**

Provider/runtime migration is complete for current sources. Key migration PRs: #24-#32, #50, #52, #54.

Source-state/report/evaluation work includes PRs #34-#48, #70, #85 and #87. The retained projection has typed states/reasons, observation counts, attempt/terminal flags, state/reason counts and deterministic evaluation counters with explicit attempt/failure/no-match/yield semantics. Quick and converged retained paths use the same projection helper. The private case UI consumes those retained fields directly. Historical cases created before the projection existed are not backfilled with guessed state.

Document-intake/review checkpoints:

- PR #56: deterministic candidate character spans and fail-closed reviewed identifier promotion;
- PR #58: extraction-time PDF page spans and corrected flattened-text limits;
- PR #60: short-lived server-owned candidate review state without raw-document retention;
- PR #62/#63: atomic confirm/reject/re-review/promotion with immutable candidate value/provenance;
- PR #64: authenticated + CSRF-protected HTTP review actions;
- PR #66: separate explicit retained-case execution from a currently confirmed, research-authorized server-owned candidate;
- PR #83: private operator controls for confirm/reject/re-review/promotion preview and separate explicit converged-case execution;
- PR #87: retained reviewed-document seed provenance and source execution/evaluation state are visible in private case views without moving authorization into the browser.

Architecture/privacy closure checkpoints:

- PR #68: catalog/binding/registry/shared-runtime ownership and zero-spend invariants; ADR 0040;
- PR #70: convergence requires canonical typed source-run reports; ADR 0041;
- PR #72: complete quick-provider payloads have one retained owner; ADR 0042;
- PR #74: M5 candidate provenance references canonical node observations; ADR 0043;
- PR #77: converged pivot provenance uses canonical observation/decision references; ADR 0044;
- PR #79: quick connected fields use canonical observation references; ADR 0045;
- PR #81: private UI resolves canonical quick/converged references and API response hydration is removed; ADR 0046;
- PR #83: private upload-review UI preserves server-owned review/execution authority; ADR 0047;
- PR #85: quick/converged source visibility and evaluation use one retained privacy-bounded projection; ADR 0048;
- PR #87: private case UI consumes retained seed provenance/source state/evaluation directly and treats missing historical state as unavailable; ADR 0049.

## Source-run semantics

Retained source-run projections carry logical source name, lead kind, state/reason, observation count and execution/terminal flags plus deterministic aggregate/per-source counters. They do not duplicate identifier values, source locators, provider payloads, secrets, exception text or timing data.

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

`source_provider_exception_record()` is the governed provider-exception mapping authority. Warnings are human context only and are never parsed into source state. Source-evaluation counters are descriptive counts, not provider reliability probabilities or identity-quality scores.

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

Run the final V2-D architecture/compatibility/privacy/documentation/zero-spend closure audit. Do not add another provider during this audit.

The audit must verify, from executable code and regression tests rather than documentation claims alone:

1. source catalog ↔ executable binding ↔ provider registry ↔ process-wide runtime ownership consistency;
2. retained-report single ownership, canonical provenance references and explicit read-only historical compatibility;
3. upload candidate extraction → human review → promotion → separate explicit case execution authority;
4. typed source-state/evaluation semantics, phase-proven attempt accounting and private UI consumption without warning inference;
5. required baseline functionality with zero paid APIs/hosting/database/proxy/enrichment, while optional Brave remains non-required;
6. roadmap, ADR numbering, continuity checkpoint and tests matching current executable behavior with no stale compatibility seam that can bypass the newer contracts.

If the audit finds a material inconsistency, fix it before declaring closure. If the audit is clean, record an explicit V2-D closure checkpoint before reviewing or activating any new third-party provider/API.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
