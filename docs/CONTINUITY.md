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
- Main before PR #100: `f73cf61813045b84ade6d5d378bf2078609169ce`
- PR #100 exact tested head: `3bbfdf9afbee752417eaa64ec3c4af102c0b69ed`
- PR #100 exact-head CI: run `32197849901`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #100 merge: `e7807fca1908eba420cd1a88e44136cf34d6c59d`
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`
- Zero-spend operating runbook: `docs/ZERO_SPEND_RUNBOOK.md`
- Optional paid Render reference: `deploy/render-paid.yaml`

## Milestone state

- M0-M6: complete.
- M7 private one-admin product: implemented and manually accepted locally.
- M8 privacy lifecycle/operations: substantially implemented; hosted backup/restore remains deferred until a persistent hosted store is selected.
- M9 private convergence: implemented.
- V2-A typed lead graph: complete, PR #20.
- V2-B deterministic frontier: complete, PR #21.
- V2-C source capability registry/planner: complete, PR #22.
- V2-D runtime consistency and architecture closure: complete, PRs #89-#90, ADRs 0050-0051.
- M10: source-state fixtures, graph-limit comparison and multi-kind labelled synthetic cohort support exist. Source-attempt/yield cost modelling, consented/representative cohorts, replay/ablation and threshold analysis remain before any recursion/threshold change.
- Post-V2-D source expansion: Bluesky public profiles are active for valid AT handles through the governed runtime, PR #98 / ADR 0055.

## Latest block — broadened M10 labelled cohort

PR #100 expands the deterministic M10 cohort without adding a provider or changing production policy.

The reusable fixture library now spans four executable seed kinds:

- username;
- email;
- URL;
- reviewed phone.

Six fixture families cover depth-limited traversal, duplicate suppression, provider failure, email → URL → username traversal, URL traversal with a review-only phone clue, and a reviewed-phone seed path. M10 cohort aggregation now also retains `review_required`, `display_only` and `blocked` counts instead of dropping those non-executing policy outcomes.

### Controlled comparison

Using the real `LeadFrontier` through `compatibility_frontier_limits`:

Current policy — depth 2 / 12 nodes:

- 6 fixtures;
- 15 total nodes / 9 added nodes;
- 9 labelled admitted pivots;
- 8 relevant pivots;
- 1 wrong pivot;
- 2 duplicate suppressions;
- 2 provider failures;
- 3 budget stops;
- 1 review-required decision.

Candidate policy — depth 3 / 12 nodes:

- 18 total nodes / 12 added nodes;
- 12 labelled admitted pivots;
- 8 relevant pivots;
- 4 wrong pivots;
- the three extra admitted pivots are all labelled wrong in this synthetic cohort;
- no additional relevant pivot is gained;
- the three depth budget stops disappear.

This is deterministic fixture evidence, not population evidence. It strengthens the case for leaving production at depth 2 / 12 nodes, but it does not establish an optimal recursion policy.

### Corrected assumptions during PR #100

1. The earlier cohort was too username-heavy to support broader product conclusions. M10 now includes email, URL and reviewed-phone seed shapes.
2. Cohort aggregation previously omitted review/display/blocked states even though the production frontier tracks them. Those counts now survive aggregation.
3. More graph reach is not automatically more useful. In this controlled cohort, depth 3 adds three pivots and all three are wrong-labelled while relevant-pivot count stays flat.
4. The cohort still does not model provider request-cost units or money. It must not be used to claim that a larger frontier is operationally cheap or expensive yet.

ADR 0056 records the decision and limits.

## Permanent evidence semantics

- Observations, factual Claims and correlation results remain separate.
- Every factual conclusion keeps provenance.
- A discovered clue is a research lead, not proof of identity.
- Same-handle reuse alone is weak evidence.
- M5 is deterministic evidence-strength triage, not identity probability.
- `calibration_status=uncalibrated` and `is_identity_claim=false` remain fixed.
- Contradictions/vetoes and stale evidence remain visible.
- Unknown, not-found, withheld, unavailable, blocked and budget-stopped remain distinct outcomes.
- No AI/ML/embedding/biometric identity decision is in the correlation path.

## Permanent security, privacy and cost boundary

Allowed scope is attributable public information and explicitly authorized data. PersonaLattice does not add private-account bypass, login/account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

The required baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Brave remains optional/metered; no `BRAVE_SEARCH_API_KEY` means no Brave attempt. Bluesky requires no credential or paid service and is not a single point of failure for the zero-spend path.

Uploaded content is untrusted data. Extraction is never execution authority. A candidate becomes externally research-authorized only after explicit human confirmation, and only a separate explicit run action may start research.

## Stable architecture

- Next.js private/public UI: `apps/web`
- FastAPI API: `services/api`
- evidence/persistence/normalization: `services/api/app/evidence`
- bounded file intake + review: `services/api/app/uploads`
- upload-review HTTP boundary: `services/api/app/upload_review_api.py`
- reviewed-candidate case execution: `services/api/app/uploads/research_service.py`
- governed provider execution: `services/api/app/providers`
- process-wide provider ownership: `services/api/app/providers/shared_runtime.py`
- deterministic correlation: `services/api/app/correlation`
- convergence: `services/api/app/convergence.py`
- retained converged reference validation: `services/api/app/converged_report.py`
- typed leads/frontier/source planning/reporting/evaluation: `services/api/app/intelligence`
- M10 cohort aggregation: `services/api/app/intelligence/m10_cohort.py`
- M10 reusable multi-kind fixture library: `services/api/app/intelligence/m10_fixture_library.py`
- quick structured-report references: `services/api/app/reporting.py`
- quick research: `services/api/app/research.py`
- retained cases: `services/api/app/cases.py`
- private case view: `apps/web/app/admin/quick-research.tsx`
- private upload-review UI: `apps/web/app/admin/upload-review-workflow.tsx`
- source expansion design: `docs/V2_SOURCE_EXPANSION_PLAN.md`

## Closed V2-D invariants

### Source execution ownership

Current network execution is governed for Sherlock, GitHub, GitLab, Codeforces, Bluesky (valid AT handles only), public DNS and optional Brave exact-match search. The executable legacy-network allowance is empty.

Catalog, executable binding, provider registry and process-wide runtime ownership are checked symmetrically. Planned/review/manual/reference sources remain non-executable. Required active recursive sources must be zero-spend eligible; a non-zero-spend recursive source can only be optional.

### Source-run semantics

Retained source-run projections carry logical source name, lead kind, typed state/reason, observation count and execution/terminal flags plus deterministic aggregate/per-source counters. They do not duplicate identifier values, source locators, provider payloads, secrets, exception text or timing data.

Critical distinctions:

- completed call with results → `executed / results_returned`;
- completed call with zero results → `not_found / no_match`;
- completed neutral withholding → `withheld / public_web_opt_out` or `withheld / account_unavailable`, attempted but not failure;
- optional source absent → `unavailable / optional_not_configured`, no attempt;
- local budget stop → `budget_stopped / local_budget`, no provider contact;
- provider-policy rejection → blocked, no attempt;
- required server-side secret absent → unavailable, no attempt;
- remote rate limit / proven execution failure → unavailable, attempted;
- returned malformed result → unavailable, attempted only when post-attempt phase is mechanically proven;
- generic `ProviderValidationError` → no source-run record because its phase is ambiguous.

Warnings are human context only and are never parsed into source state. Evaluation counters are descriptive counts, not provider reliability probabilities or identity-quality scores.

### Retained privacy ownership

Complete provider evidence and provenance have canonical retained owners. Quick connected fields, M5 candidate provenance, converged lead decisions and admitted edges use validated canonical references where duplicate value/locator retention is unnecessary. Historical self-contained formats remain readable through explicit read-only compatibility; compatibility copies are not written back into new retained data.

### Reviewed-document authority

Extraction creates candidates only; short-lived server-owned review state owns authorization; review mutation cannot alter candidate value/provenance; promotion does not call providers; only a separate authenticated, CSRF-protected explicit case-run action can reload current trusted state and begin research.

## Current deliberate limits

- convergence max depth: 2;
- convergence max nodes: 12;
- newly discovered phone leads require review;
- contextual name/organization/location remain non-autonomous;
- public-search snippets do not become automatic identifier leads;
- Brave remains optional and excluded from required zero-spend operation;
- Bluesky is applicable only to syntactically valid AT handles, not arbitrary usernames;
- no identity probability or universal-account claims.

## Next gate

Do not reopen V2-D architecture casually and do not change recursion because a synthetic cohort looks convenient.

The highest-value next M10 block is explicit source-attempt / observation-yield / request-cost-unit accounting for fixtures. Keep monetary cost separate unless an actual provider has a reviewed price model. This is needed before comparing the operational burden of larger frontier policies.

A separate acceptable track is fresh review of exactly one zero-spend candidate from `docs/V2_SOURCE_EXPANSION_PLAN.md`. Gravatar, WebFinger/ActivityPub and RDAP remain candidates, not permissions; fresh official terms, cost, authentication, fields, contact risk and retention review are required before activation.

Before any production recursion or M5-threshold change, M10 still needs broader consented/representative cohorts, deterministic replay/factor ablations and defensible labelled false-positive/false-negative analysis. Production limits remain depth 2 / 12 nodes.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
