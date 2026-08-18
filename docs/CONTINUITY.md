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
- Main before the Bluesky admission block: `b15fb8f9cc9f450e8fb5b82ba74414c4b4e7618f`
- PR #94 exact tested head: `da52f06d15926000f287691d5342a98e5b265ffd`
- PR #94 CI: run `32182933798`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #94 merge: `2dc1b84fb50808168d52b76c1a9530e0be378ac1`
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
- M10: deterministic single-fixture evaluation plus labelled cohort comparison exist; broader representative cohorts, replay/ablation and defensible threshold analysis remain before any recursion/threshold change.
- Post-V2-D source expansion: Bluesky admission preflight complete; Bluesky network execution remains disabled.

## Latest block — Bluesky public-web admission preflight

PR #94 adds `services/api/app/providers/bluesky_admission.py`, regression coverage in `services/api/tests/test_bluesky_admission.py`, and ADR 0053.

This block intentionally does **not** register, bind or execute a Bluesky provider. `bluesky_public_profile` remains `PLANNED`, `source_policy_reviewed=False` and `recursive_eligible=False`.

The admission contract closes two source-specific gaps before activation:

1. PersonaLattice's generic `username` lead is broader than an AT Protocol handle. Only real-world DNS-shaped AT handles are admissible for a future Bluesky call. Generic usernames, `@`-prefixed UI forms, malformed handles and reserved/non-public TLDs fail locally before network execution.
2. Bluesky's `!no-unauthenticated` label is a public-web opt-out. It is now represented by a distinct local `BlueskyPublicWebOptOut` decision in the admission layer. It must not later be collapsed into `not_found` or provider failure.

The reviewed future retained field set is intentionally small: DID, normalized handle and optional display name, plus explicit account-candidate/non-identity/public-visibility flags. Description, avatar, follower/follow/post counts, viewer state and arbitrary response fields are excluded.

Official Bluesky/AT Protocol material was rechecked on 2026-08-19: `app.bsky.actor.getProfile` is public/unauthenticated; public AppView calls should prefer `https://public.api.bsky.app`; AT handles use DNS-hostname syntax and lowercase normalization; `!no-unauthenticated` means content is unavailable to logged-out clients that respect the label; current Bluesky terms remain the governing service terms. Recheck again at activation rather than treating this checkpoint as permanent policy authority.

## M10 labelled cohort checkpoint

PR #92 added `services/api/app/intelligence/m10_cohort.py` and ADR 0052. Cohort fixtures run through the production `LeadFrontier` rather than a second scheduler and aggregate deterministic graph-growth, duplicate, provider-failure, budget-stop and labelled relevant/wrong-pivot counts.

The current controlled cohort contains a depth-limited chain, duplicate-heavy output and a provider-failure path. Moving that fixture cohort from depth 2 / 12 nodes to depth 3 / 12 nodes admits one extra node, but the extra admitted pivot is labelled wrong and adds no relevant pivot. This is regression-fixture evidence, not population evidence.

Production recursion therefore remains **depth 2 / 12 nodes**.

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
- Bluesky pre-network admission: `services/api/app/providers/bluesky_admission.py`
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

Critical current distinctions:

- completed call with results → `executed / results_returned`;
- completed call with zero results → `not_found / no_match`;
- optional source absent → `unavailable / optional_not_configured`, no attempt;
- local budget stop → `budget_stopped / local_budget`, no provider contact;
- provider-policy rejection → blocked, no attempt;
- required server-side secret absent → unavailable, no attempt;
- remote rate limit / proven execution failure → unavailable, attempted;
- returned malformed result → unavailable, attempted only when post-attempt phase is mechanically proven;
- generic `ProviderValidationError` → no source-run record because its phase is ambiguous.

Bluesky activation will require one additional truthful distinction: a returned `!no-unauthenticated` profile is an **attempted public-web opt-out**. The local admission type exists after PR #94, but the shared typed source-run vocabulary has not yet been extended. Do not fake this as not-found or provider failure to make activation easier.

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
- Bluesky remains non-executable after the admission preflight;
- no identity probability or universal-account claims.

## Next gate

Do not reopen V2-D architecture casually.

The next bounded source-expansion block can implement the Bluesky network adapter, but it must do all activation work atomically:

1. call only the unauthenticated public `app.bsky.actor.getProfile` route on the reviewed public AppView host;
2. preserve the PR #94 handle and field-admission contract;
3. distinguish profile-not-found from suspension/deactivation, malformed output, remote rate limit and transient failure;
4. extend the typed source-outcome vocabulary so `!no-unauthenticated` is an attempted public-web opt-out, not not-found and not a provider reliability failure;
5. add deterministic success/not-found/opt-out/malformed/rate-limit/unavailable fixtures;
6. move Bluesky from PLANNED to current execution only when catalog + binding + registry + process-wide `ProviderRuntime` + quick-research integration agree in the same PR;
7. recheck current official terms/quota/cost immediately before activation.

M10 still needs broader labelled synthetic/consented cohorts across more lead kinds and source-yield/cost shapes, deterministic replay/factor ablations, and defensible labelled threshold analysis before any production recursion or M5-threshold change.

Production stays depth 2 / 12 nodes until that evidence exists.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
