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
- Main before PR #105: `d8c5cbc8179e01624d9a40ccb9f3ae3a67ae537b`
- PR #105: execute replay-anchored M10 factor ablations through the production M5 engine
- Exact tested implementation/docs head: `0722100bae694e2cb55588b7f6150628f43c9bcd`
- Exact-head CI: run `32212903112`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #105 merge: `2fa6d4b061f48b63f24696c30e0da582ccf4b3d8`
- ADR: `docs/decisions/0060-m10-factor-ablation-execution.md`
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
- M10: source-state fixtures, graph-limit comparison, multi-kind labelled synthetic cohort support, provider-boundary source-attempt/yield/request-cost accounting, deterministic replay fingerprints, replay/policy-anchored factor-ablation manifests and real-engine factor-ablation execution now exist. Broader defensible cohorts, reusable cross-run M5 case identity and threshold analysis remain before any recursion/threshold change.
- Post-V2-D source expansion: Bluesky public profiles are active for valid AT handles through the governed runtime, PR #98 / ADR 0055.

## Latest block — real-engine M5 factor ablation execution

PR #105 executes the ADR 0059 omission manifest through the production `CorrelationEngine` rather than implementing a second scoring policy inside M10.

Execution behavior:

- validates the exact replay/policy-anchored ablation plan before running;
- changes only the `CorrelationRequest.factors` tuple;
- records baseline and ablated M5 outcome, evidence score and positive independence-group count plus deltas;
- keeps every omission diagnostic-only;
- keeps veto omissions such as `hard_contradiction` safety-critical;
- represents a factor absent from a controlled case as an explicit no-op result;
- accepts multiple controlled cases so contradiction-veto behavior does not mask positive-factor sensitivity.

A review issue was corrected before merge: `CorrelationEngine` normally persists `CorrelationRun` and factor rows. Each M10 diagnostic call now runs inside a nested transaction that is rolled back after the result is materialized. Regression coverage proves no M10 diagnostic correlation/factor rows remain in the supplied evidence database.

The execution report is in-memory M10 output. It does not expand retained case data.

### Controlled M5 sensitivity cases

Current controlled results under `m5-evidence-strength-v1`:

- `possible_metadata_temporal`: baseline `possible_match`, score 35; omit compatible profile metadata → `insufficient_evidence`, score 20, delta `-15`;
- `strong_exact_identifier`: baseline `strong_candidate`, score 75; omit exact confirmed identifier overlap → `insufficient_evidence`, score 20, delta `-55`;
- `strong_independent_cross_link`: baseline `strong_candidate`, score 70; omit independent cross-link → `possible_match`, score 35, delta `-35`;
- `contradiction_veto`: baseline `contradicted`, score 0; diagnostic omit hard contradiction → `strong_candidate`, score 90, delta `+90`.

The hard-contradiction result demonstrates veto sensitivity only. It is not evidence that the veto should be removed. No M5 weight, threshold, veto, calibration status or identity semantic changed.

One deliberate limitation remains: these controlled M5 cases are created from semantic test setup but are not yet a separately versioned/fingerprinted fixture specification independent of generated database UUIDs. Do not overstate this block as complete cross-run experiment provenance or calibration.

## Current controlled graph M10 result

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

Delta depth 2 → depth 3 in this synthetic cohort: +3 source attempts, +3 request-cost units, +3 observation-yield units, +3 admitted pivots, +3 wrong-labelled pivots and +0 relevant pivots.

This is synthetic fixture evidence, not population evidence or monetary cost. It supports leaving production recursion unchanged; it does not establish an optimal policy.

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
- M10 replay identity: `services/api/app/intelligence/m10_replay.py`
- M10 factor-ablation identity: `services/api/app/intelligence/m10_factor_ablation.py`
- M10 real-engine ablation execution: `services/api/app/intelligence/m10_factor_ablation_execution.py`
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

Do not reopen V2-D architecture casually. Do not raise production recursion from the current synthetic evidence, and do not treat the safety-critical hard-contradiction ablation as a production recommendation.

The preferred next M10 block is to define **stable semantic identities for reusable controlled M5 ablation fixtures that do not depend on generated database UUIDs**, then fingerprint the case set and execution result for cross-run reproducibility. After that, broaden consented or otherwise defensibly labelled cohorts and perform threshold/error analysis where labels support it.

A separate acceptable track is fresh review of exactly one zero-spend source candidate from `docs/V2_SOURCE_EXPANSION_PLAN.md`. Gravatar, WebFinger/ActivityPub and RDAP remain candidates, not permissions; current official terms, cost, authentication, fields, contact risk and retention review are required before activation.

Production limits remain depth 2 / 12 nodes. M5 remains uncalibrated evidence-strength triage, not identity probability.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
