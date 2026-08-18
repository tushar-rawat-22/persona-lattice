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
- Main before PR #98: `f39a50c78e81b4b1605e0035ca2261e28808e2e3`
- PR #98 exact tested head: `41e71c35fdb5771c63e5ce589b5f149f59861437`
- PR #98 exact-head CI: run `32193906435`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #98 merge: `720c1d11af92007a6f3f6fc913ea6544d52bb4e3`
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
- Post-V2-D source expansion: Bluesky public profiles are active for valid AT handles through the governed runtime, PR #98 / ADR 0055.

## Latest block — Bluesky governed runtime activation

PR #98 activates the previously reviewed Bluesky adapter without reopening V2-D:

- `bluesky_public_profile` is now active, source-policy reviewed and recursive-eligible;
- the provider descriptor is `DEVELOPMENT`, credentialless and bounded to one attempt, 4s timeout, 64 KiB result ceiling, concurrency 2 and a local 30/60s application budget;
- the exact adapter instance is owned by the process-wide `ProviderRuntime`;
- the source is bound for `USERNAME`, but actual execution is value-gated by the existing AT-handle admission contract;
- ordinary usernames, malformed handles and `@handle` UI forms are non-applicable and cause no Bluesky call, source-run record or fabricated failure;
- valid AT handles use the public `app.bsky.actor.getProfile` route;
- successful observations retain only DID, normalized handle, optional display name and account-candidate/non-identity/public-visibility flags;
- profile URL is canonical provenance, not an emitted URL lead;
- catalog `emits` is therefore `USERNAME + NAME`, correcting the older planned overclaim that included URL/location;
- `withheld / public_web_opt_out` and `withheld / account_unavailable` remain completed neutral attempts, not provider failures or `not_found`;
- ADR 0055 records the activation and its latency/concurrency tradeoff.

Fresh official/primary review immediately before activation reconfirmed unauthenticated public AppView access, DNS-style handle semantics, `!no-unauthenticated` public-web opt-out behavior and the public AppView operating model. Bluesky's current Terms of Service and AT Protocol Network Services privacy notice were also reviewed. Public status does not override explicit opt-out or authorize nonpublic collection.

### Corrected assumptions during PR #98

1. Generic `USERNAME` does not imply Bluesky applicability. A plain value such as `alice` must not be sprayed into the provider.
2. The planned source catalog overstated Bluesky outputs. The admitted adapter does not expose location, and source-locator provenance is not an automatic URL lead; `emits` was narrowed to username + display-name context.
3. CI initially failed with 403 passed / 2 failed because two tests still asserted the intentional pre-activation `PLANNED` state. Those stale tests were updated to assert the new reviewed/governed activation contract; the final exact head then passed full CI.
4. The first activation keeps Bluesky sequential after the existing parallel GitHub/GitLab/Codeforces enrichment block. This is a deliberate conservative rollout choice; optimize only from measured latency/yield evidence.
5. No Bluesky test-only injection seam was added to production quick research. Runtime-path tests patch the governed runtime boundary instead.

## M10 checkpoint

PR #92 established count-only cohort aggregation through the production `LeadFrontier`. The controlled cohort includes depth-limited, duplicate-heavy and provider-failure shapes.

In that fixture cohort, moving from depth 2 / 12 nodes to depth 3 / 12 nodes admits one additional node, but the extra pivot is labelled wrong and adds no relevant pivot. This is fixture evidence, not population evidence.

Production recursion therefore remains **depth 2 / 12 nodes**.

Bluesky withheld states remain separate from provider failure so future reliability measurements are not contaminated by user visibility choices or account state.

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
- Bluesky admission: `services/api/app/providers/bluesky_admission.py`
- Bluesky governed adapter: `services/api/app/providers/bluesky_public.py`
- process-wide provider ownership: `services/api/app/providers/shared_runtime.py`
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

`source_provider_exception_record()` remains the governed provider-exception mapping authority. Warnings are human context only and are never parsed into source state. Evaluation counters are descriptive counts, not provider reliability probabilities or identity-quality scores.

### Retained privacy ownership

Complete provider evidence and provenance have canonical retained owners. Quick connected fields, M5 candidate provenance, converged lead decisions and admitted edges use validated canonical references where duplicate value/locator retention is unnecessary. Historical self-contained formats remain readable through explicit read-only compatibility; compatibility copies are not written back into new retained data.

### Reviewed-document authority

The chain is server-owned and explicit: extraction creates candidates only; short-lived review state owns authorization; review mutation cannot alter candidate value/provenance; promotion does not call providers; only a separate authenticated, CSRF-protected explicit case-run action can reload current trusted state and begin research.

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

Do not reopen V2-D architecture casually and do not activate another provider from an old plan alone.

Choose one bounded next block:

1. broaden M10 labelled synthetic/consented cohorts across additional lead kinds and source-yield/cost shapes; or
2. review exactly one next zero-spend candidate from `docs/V2_SOURCE_EXPANSION_PLAN.md` using fresh official terms, cost, authentication, returned-field, contact-risk and retention review before any activation.

Gravatar, WebFinger/ActivityPub and RDAP remain candidates, not permissions. Paid or metered sources remain optional only.

Before any production recursion or M5-threshold change, M10 still needs broader representative cohorts, deterministic replay/factor ablations and defensible labelled false-positive/false-negative analysis. Production limits remain depth 2 / 12 nodes.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
