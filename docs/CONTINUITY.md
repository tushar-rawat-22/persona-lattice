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
- Main before PR #96: `2e36b274a2d87b5c706bad10a4866dddf754395e`
- PR #96 exact tested head: `277aea3f80f4d0faf3d2bcde3a8fe9fceec1576c`
- PR #96 exact-head CI: run `32189304220`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #96 merge: `43590e00b989a101a70c3fd44fd0c96ec6161e1f`
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
- M10: deterministic source-state fixtures, labelled graph evaluation and initial multi-fixture cohort comparison exist. Broader representative cohorts, replay/ablation and defensible threshold analysis remain before any recursion/threshold change.
- Post-V2-D source expansion: Bluesky admission plus bounded adapter/outcome contract complete; Bluesky execution remains disabled pending atomic activation.

## Latest block — Bluesky bounded adapter + neutral attempted outcomes

PR #96 adds:

- `services/api/app/providers/bluesky_public.py`;
- planned provider descriptor metadata for `bluesky_public_profile`;
- typed `withheld` source-run state;
- `public_web_opt_out` and `account_unavailable` reasons;
- M10 counters that treat withheld responses as completed attempts but not failures;
- deterministic Bluesky adapter/outcome tests;
- ADR 0054.

This block intentionally does **not** activate Bluesky. The source catalog remains `PLANNED`, `source_policy_reviewed=False`, `recursive_eligible=False`; there is no source binding, process-wide runtime owner or quick-research call.

Fresh official/primary-source review on 2026-08-19 reconfirmed:

- public `app.bsky.actor.getProfile` reads are unauthenticated;
- the cached public AppView host is `https://public.api.bsky.app` for public-web clients;
- AT Protocol handles are DNS-hostname-shaped and normalized lowercase;
- `!no-unauthenticated` is a logged-out/public-web opt-out signal;
- AppView distinguishes profile absence from account takedown/deactivation;
- public AppView limits are described as generous, so the planned descriptor keeps a conservative local 30/minute application ceiling rather than claiming a universal upstream quota.

The adapter accepts no credential, fails locally on generic usernames/`@` UI forms/malformed handles, and retains only DID, normalized handle and optional display name plus account-candidate/non-identity/public-visibility flags. Description, avatar, follower/follow/post counts, viewer state and arbitrary response fields are excluded.

### Corrected assumptions during PR #96

1. A successful provider response that refuses public-web visibility is not `not_found` and not a reliability failure. It is now `withheld / public_web_opt_out`, execution attempted = true.
2. A suspended/deactivated account response is also an attempted neutral outcome, now `withheld / account_unavailable`.
3. Exact-shape/state-matrix tests failed after the new vocabulary was introduced. The product semantics were kept; stale contracts were updated. The corrected exact head then passed full CI.
4. The first registry edit produced noisy one-line formatting. That diff was rejected and restored to normal maintainer formatting before merge.
5. `source_states.py` privacy documentation was preserved rather than allowing a semantic change to delete useful maintainer context.

## M10 checkpoint

PR #92 established count-only cohort aggregation through the production `LeadFrontier`. The current controlled cohort includes depth-limited, duplicate-heavy and provider-failure shapes.

In that fixture cohort, moving from depth 2 / 12 nodes to depth 3 / 12 nodes admits one additional node, but the extra pivot is labelled wrong and adds no relevant pivot. That is fixture evidence, not population evidence.

Production recursion remains **depth 2 / 12 nodes**.

The new Bluesky withheld state is intentionally separate from provider failure so future source reliability measurements are not contaminated by user visibility choices or account state.

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
- Bluesky pre-network admission: `services/api/app/providers/bluesky_admission.py`
- Bluesky bounded adapter, still non-executable: `services/api/app/providers/bluesky_public.py`
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
- completed neutral withholding → `withheld / public_web_opt_out` or `withheld / account_unavailable`, attempted but not failure;
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

The chain is server-owned and explicit: extraction creates candidates only; short-lived review state owns authorization; review mutation cannot alter candidate value/provenance; promotion does not call providers; and only a separate authenticated, CSRF-protected explicit case-run action can reload current trusted state and begin research.

## Current deliberate limits

- convergence max depth: 2;
- convergence max nodes: 12;
- newly discovered phone leads require review;
- contextual name/organization/location remain non-autonomous;
- public-search snippets do not become automatic identifier leads;
- Brave remains optional and excluded from required zero-spend operation;
- Bluesky remains non-executable after the adapter/outcome pre-activation block;
- no identity probability or universal-account claims.

## Next gate

Do not reopen V2-D architecture casually.

The next Bluesky block is **atomic activation**, only after another fresh official-source check at execution time:

1. keep `getProfile` on the reviewed unauthenticated public AppView route;
2. preserve the current handle admission and minimal field allowlist;
3. move source catalog policy/status, source binding, provider status, process-wide `ProviderRuntime` ownership and quick-research/source-run integration together;
4. keep success, not-found, public-web opt-out, account-unavailable, malformed, remote-rate-limit and transient/unavailable behavior deterministic and tested;
5. keep generic username spraying impossible;
6. keep the zero-spend baseline independent of Bluesky availability;
7. keep production recursion at depth 2 / 12 nodes.

M10 still needs broader labelled synthetic/consented cohorts across more lead kinds and source-yield/cost shapes, deterministic replay/factor ablations, and defensible labelled threshold analysis before any production recursion or M5-threshold change.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
