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
- Main before PR #102: `5f7b2008e6a013acce1e8a0ac6f4144e29562aa5`
- PR #102 tested implementation/documentation head before this continuity checkpoint: `c149a12e0e1e8f6bc62cf63fe0fde150ade34e8e`
- PR #102 exact-head CI: run `32201808759`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
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
- M10: source-state fixtures, graph-limit comparison, multi-kind labelled synthetic cohort support and provider-boundary source-attempt/yield/request-cost-unit accounting exist. Broader defensible cohorts, replay/ablation and threshold analysis remain before any recursion/threshold change.
- Post-V2-D source expansion: Bluesky public profiles are active for valid AT handles through the governed runtime, PR #98 / ADR 0055.

## Latest block — M10 operational request/yield accounting

PR #102 adds deterministic operational-work counters to the existing graph-limit cohort comparison without changing production research behavior.

### Accounting boundary

The important implementation detail is that source attempts are counted at the exact simulated provider boundary: after `LeadFrontier.consider()` returns `ENQUEUE`, before the fixture models provider success/failure.

This was corrected during self-review. Deriving attempts later as `admitted pivots + provider failures` is wrong because a provider call can succeed and still have its returned key rejected by `frontier.admit()` as a duplicate or post-call budget conflict. Such a call still consumed a request and produced a synthetic result.

The final evaluator therefore exposes:

- `source_attempt_count` — every fixture call that actually crosses the simulated provider boundary;
- `successful_source_attempt_count` — attempted calls with a successful fixture result, even if the resulting pivot is later not admitted;
- `zero_yield_source_attempt_count` — modelled provider failures;
- `observation_yield_unit_count` — one synthetic yield unit per successful fixture call;
- `request_cost_unit_count` — one abstract request-cost unit per attempted fixture call.

Duplicates/review/display/blocked/local budget stops that happen before provider execution consume zero request-cost units. Regression coverage also proves that a successful post-call duplicate still consumes one request-cost unit and one yield unit.

These are synthetic accounting units, not money, provider billing estimates, reliability rates or identity-quality scores.

### Controlled cohort result

Current production policy — depth 2 / 12 nodes:

- 6 fixtures;
- 15 total nodes / 9 added nodes;
- 9 labelled admitted pivots: 8 relevant, 1 wrong;
- 11 simulated source attempts;
- 9 successful/yield-producing attempts;
- 2 zero-yield provider failures;
- 11 abstract request-cost units;
- 9 observation-yield units;
- 3 local budget stops.

Candidate — depth 3 / 12 nodes:

- 18 total nodes / 12 added nodes;
- 12 labelled admitted pivots: 8 relevant, 4 wrong;
- 14 simulated source attempts;
- 12 successful/yield-producing attempts;
- 2 zero-yield provider failures;
- 14 abstract request-cost units;
- 12 observation-yield units;
- no depth budget stops.

Delta from depth 2 → depth 3 in this synthetic cohort:

- +3 source attempts;
- +3 request-cost units;
- +3 observation-yield units;
- +3 admitted pivots;
- +3 wrong-labelled pivots;
- +0 relevant pivots.

This makes the controlled tradeoff explicit: the tested deeper frontier does more simulated source work while adding no relevant labelled pivot in this cohort. It is still synthetic evidence and does not establish an optimal production policy.

ADR 0057 records the decision and limitations.

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
- graph-limit + provider-boundary operational evaluator: `services/api/app/intelligence/graph_limit_evaluation.py`
- quick research: `services/api/app/research.py`
- retained cases: `services/api/app/cases.py`
- source expansion design: `docs/V2_SOURCE_EXPANSION_PLAN.md`

## Closed V2-D invariants

Current network execution is governed for Sherlock, GitHub, GitLab, Codeforces, Bluesky (valid AT handles only), public DNS and optional Brave exact-match search. The executable legacy-network allowance is empty.

Catalog, executable binding, provider registry and process-wide runtime ownership are checked symmetrically. Planned/review/manual/reference sources remain non-executable. Required active recursive sources must be zero-spend eligible; a non-zero-spend recursive source can only be optional.

Retained source-run projections carry typed state/reason and bounded count metadata without duplicating identifier values, source locators, provider payloads, secrets, exception text or timing data. Complete provider evidence/provenance has canonical retained owners. Historical formats remain read-only compatible.

Reviewed-document extraction creates candidates only; short-lived server-owned review state owns authorization; review mutation cannot alter candidate value/provenance; promotion does not call providers; only a separate authenticated, CSRF-protected explicit case-run action can begin research.

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

Do not reopen V2-D architecture casually and do not raise production recursion. The current synthetic M10 result now shows both quality and operational-work costs moving in the wrong direction for depth 3: +3 request units, +3 yield units, +3 wrong-labelled pivots and +0 relevant pivots.

The preferred next M10 work is broader consented or otherwise defensibly labelled evaluation plus deterministic replay/factor-ablation support. Provider-specific request/yield weights should be added only where a real adapter needs more fidelity than the current one-request/one-yield fixture abstraction.

A separate acceptable track is fresh review of exactly one zero-spend source candidate from `docs/V2_SOURCE_EXPANSION_PLAN.md`. Gravatar, WebFinger/ActivityPub and RDAP remain candidates, not permissions; current official terms, cost, authentication, fields, contact risk and retention review are required before activation.

Production limits remain depth 2 / 12 nodes. M5 remains uncalibrated evidence-strength triage, not identity probability.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
