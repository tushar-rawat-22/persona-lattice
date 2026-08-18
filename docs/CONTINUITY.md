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
- Verified main before the M10 cohort block: `f38743a021ce02c21c859036d14745bc3e6f46a9`
- PR #92 exact tested implementation head: `ff76e7328b94429940fc15a508fa497b3213c6f0`
- PR #92 CI: run `32177268786`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #92 merge: `68cc880fbe26a092bd590b06da7d22b2d412367f`
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
- M10: deterministic single-fixture evaluation plus labelled cohort comparison now exist; broader representative cohorts, replay/ablation and defensible threshold analysis remain before any recursion/threshold change.

## Latest block — M10 labelled cohort foundation

PR #92 adds `services/api/app/intelligence/m10_cohort.py`, regression coverage in `services/api/tests/test_m10_labelled_cohort.py`, ADR 0052 and the matching roadmap update.

The cohort layer does not implement another scheduler. Every fixture still runs through `evaluate_graph_limit_fixture()`, which uses the production `LeadFrontier`. It aggregates deterministic counts across independent fixtures and reports candidate-minus-baseline deltas for graph size/depth, duplicate suppression, provider failures, budget stops and labelled relevant/wrong pivots.

The initial regression cohort has three intentionally different graph shapes:

1. a depth-limited chain;
2. duplicate-heavy output;
3. a provider-failure path.

Under that controlled cohort, moving from depth 2 / 12 nodes to depth 3 / 12 nodes removes one depth budget stop and admits one extra node, but the extra admitted pivot is labelled wrong and adds no relevant pivot. This is a regression fixture result, not population evidence; it reinforces that larger recursion is not automatically better.

The cohort layer is deliberately count-only. It does not publish reliability percentages, confidence intervals, identity probability or a production-limit recommendation. Empty cohorts, duplicate fixture names and duplicate scenario names fail closed, and underlying fixture-truth validation remains authoritative.

Production recursion remains **depth 2 / 12 nodes**.

## Source expansion review checkpoint

Bluesky was re-reviewed from current official sources during the PR #92 block but was **not activated**.

Current official behavior supports a public unauthenticated AppView profile lookup and makes the public AppView suitable for public-web clients. However, Bluesky's public-web guidance also requires respecting the profile `!no-unauthenticated` self-label. A naive adapter that accepts every returned public profile would therefore violate the intended public-web boundary.

Bluesky remains `PLANNED`, `source_policy_reviewed=False`, `recursive_eligible=False` until an adapter explicitly enforces that opt-out and has deterministic success/not-found/malformed/rate-limit/unavailable/opt-out fixtures. Do not change catalog/binding/registry/runtime membership merely because the endpoint is public.

Recheck official Bluesky documentation/terms again at activation time rather than treating this checkpoint as permanent pricing/policy authority.

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
- M10 labelled cohort comparison: `services/api/app/intelligence/m10_cohort.py`
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

## Next gate

Do not reopen V2-D architecture casually.

The next source-expansion block can return to Bluesky, but activation must first make `!no-unauthenticated` enforcement a tested fail-closed adapter rule and recheck current official terms/quota/cost at that time. It still must enter through catalog + binding + registry + shared `ProviderRuntime` + typed source-state reporting + canonical evidence ownership. No hard-coded bypass in `research.py` is acceptable.

In parallel, M10 still needs broader labelled synthetic/consented cohorts across more lead kinds and source-yield/cost shapes, deterministic replay/factor ablations, and defensible labelled threshold analysis before any production recursion or M5-threshold change.

Production stays depth 2 / 12 nodes until that evidence exists.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
