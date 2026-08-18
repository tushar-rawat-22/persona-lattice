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
- Verified main after PR #90: `716be3e042a3b3e3d1216297ffed4f576034a7cf`
- PR #89 exact tested head: `f4e5ceb70bde7867cfcb07bc57459da19e023b3a`
- PR #89 CI: run `32171892313`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #89 merge: `bde651cb4249410b543b5c4accb283edfc262bab`
- PR #90 exact tested head: `d7bd2c802417e56584fad15602bd420733f077ea`
- PR #90 CI: run `32172134510`, full success across the same matrix
- PR #90 merge / verified main: `716be3e042a3b3e3d1216297ffed4f576034a7cf`
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`
- Zero-spend operating runbook: `docs/ZERO_SPEND_RUNBOOK.md`
- Optional paid Render reference: `deploy/render-paid.yaml`

## Milestone state

- M0-M6: complete.
- M7 private one-admin product: implemented and manually accepted locally.
- M8 privacy lifecycle/operations: substantially implemented; hosted backup/restore is intentionally deferred until a persistent hosted store is actually selected.
- M9 private convergence: implemented.
- V2-A typed lead graph: complete, PR #20.
- V2-B deterministic frontier: complete, PR #21.
- V2-C source capability registry/planner: complete, PR #22.
- **V2-D runtime consistency and architecture closure: complete, PRs #89-#90, ADRs 0050-0051.**
- M10: deterministic evaluation contracts exist; representative labelled evaluation remains before any recursion/threshold change.

## V2-D closure findings

The final audit did not pass on first inspection. Two real defects were fixed before closure:

1. the repository-root `render.yaml` still made a paid Render `starter` + persistent-disk topology look like the default deployment contract even though the product rule requires a zero-spend baseline;
2. runtime consistency tests proved governed binding → runtime ownership, but did not prove the reverse direction that every `ProviderStatus.DEVELOPMENT` provider is a current governed binding/runtime member.

PR #89 repaired both. Local one-admin operation is now the default zero-spend authority, the paid Render design is an explicit optional reference under `deploy/`, CI forbids a root paid Blueprint, and development provider membership must exactly match current governed binding/runtime membership. PR #89 also added an objective unique/contiguous ADR-numbering guard after an earlier duplicate-ADR incident exposed that documentation weakness.

Render's current official Blueprint documentation was rechecked during the audit: custom Blueprint filenames/paths are supported, so keeping the optional paid reference at `deploy/render-paid.yaml` is a valid deliberate separation rather than a dead file. Recheck current hosting cost/terms again before any future deployment.

ADR 0050 records zero-spend deployment authority. ADR 0051 records V2-D closure and its non-authorizations.

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

The required baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Brave remains optional/metered; no `BRAVE_SEARCH_API_KEY` means no Brave attempt.

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

## Closed V2-D invariants

### Source execution ownership

Current network execution is governed for Sherlock, GitHub, GitLab, Codeforces, public DNS and optional Brave exact-match search. The executable legacy-network allowance is empty.

Catalog, current executable binding, provider registry and process-wide runtime ownership are checked symmetrically. Planned/review/manual/reference sources remain non-executable. Required active recursive sources must be zero-spend eligible; a non-zero-spend recursive source can only be optional.

### Source-run semantics

Retained source-run projections carry logical source name, lead kind, typed state/reason, observation count and execution/terminal flags plus deterministic aggregate/per-source counters. They do not duplicate identifier values, source locators, provider payloads, secrets, exception text or timing data.

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

`source_provider_exception_record()` is the governed provider-exception mapping authority. Warnings are human context only and are never parsed into source state. Evaluation counters are descriptive counts, not provider reliability probabilities or identity-quality scores.

### Retained privacy ownership

Complete provider evidence and provenance have canonical retained owners. Quick connected fields, M5 candidate provenance, converged lead decisions and admitted edges use validated canonical references where duplicate value/locator retention is unnecessary. Historical self-contained formats remain readable through explicit read-only compatibility; compatibility copies are not written back into new retained data.

### Reviewed-document authority

The chain is server-owned and explicit:

1. bounded document/image extraction produces candidate data only;
2. deterministic character/page provenance is retained where mechanically known;
3. review candidates live in short-lived server-owned state without raw-document retention;
4. confirm/reject/re-review/promotion mutate only review/authorization state, never candidate value/provenance;
5. authenticated + CSRF-protected HTTP routes accept candidate/artifact IDs rather than browser-supplied authorization data;
6. promotion yields a typed reviewed lead but does not call providers;
7. a separate explicit case-run action reloads trusted current review state, rechecks purpose/consent, then may start research;
8. retained reviewed-document seed provenance and typed source-state/evaluation are visible in the private UI without recreating policy in the browser.

## Current deliberate limits

- convergence max depth: 2;
- convergence max nodes: 12;
- newly discovered phone leads require review;
- contextual name/organization/location remain non-autonomous;
- public-search snippets do not become automatic identifier leads;
- Brave remains optional and excluded from required zero-spend operation;
- no identity probability or universal-account claims.

## Next phase

V2-D is closed. Do not add another hard-coded source branch or reopen its architecture casually.

The next phase is reviewed source expansion, but provider activation must remain one bounded source at a time. Before activation, re-check current primary documentation, terms, quotas, cost, authentication, returned fields, contact risk and retention implications. A source appearing in `V2_SOURCE_EXPANSION_PLAN.md` is not permission to execute it.

For each future source, require catalog + policy + governed adapter + deterministic fixtures + typed source-state reporting + canonical evidence ownership. Metered/credentialed sources must remain optional, and PersonaLattice must keep working when they are absent.

M10 remains the gate for raising production recursion or changing correlation thresholds. Production stays depth 2 / 12 nodes until labelled evaluation supports a change.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
