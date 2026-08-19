# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only
- Main before PR #111: `2b13a2bf8a4e79f4d8ef2ffa10d01bc95dcce0fe`
- PR #111: consented-only M10 scenario accounting
- Exact tested PR #111 head: `f48fdf6e4b2bcfbfd8ef6f7205c1d58a04a83c68`
- Exact-head CI: run `32223948991`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #111 merge: `aa9ee406a41b7f4e36af2d1e6038a4cd85f7641b`
- ADR: `docs/decisions/0063-consented-m10-scenario-accounting.md`
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`
- Zero-spend runbook: `docs/ZERO_SPEND_RUNBOOK.md`
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
- Post-V2-D source expansion: Bluesky public profiles active for valid AT handles through the governed runtime, PR #98 / ADR 0055.
- M10: deterministic source-state fixtures, graph-limit comparison, multi-kind synthetic cohorts, attempt/yield/request-cost accounting, replay fingerprints, real-engine factor ablations, UUID-independent controlled M5 fixture replay, label-provenance manifests and consented-only scenario accounting are implemented. Representative consented evaluation and calibration remain incomplete.

## Latest block — consented-only M10 scenario accounting

PR #111 adds `services/api/app/intelligence/m10_consented_analysis.py`.

The boundary deliberately refuses to produce analysis from the current synthetic regression cohort. It requires:

- every fixture provenance basis to be `consented`;
- exact replay/fixture/provenance agreement through the existing label-manifest builder;
- every admitted pivot in every scenario to have an explicit label;
- scenario names to remain unique;
- admitted label counters to remain internally consistent.

For an eligible cohort it records exact scenario-level counts:

- declared relevant and wrong labels;
- admitted relevant and wrong pivots;
- relevant labels not admitted;
- wrong labels not admitted.

It also exposes exact numerator/denominator pairs for:

- wrong admitted pivots / labelled admitted pivots;
- admitted relevant pivots / declared relevant labels.

These are count fractions only. They are not population false-positive/false-negative rates, calibration, confidence, identity probability or evidence that the consented cohort is representative. Zero denominators produce no fraction rather than a fabricated zero rate.

The analysis digest is anchored to the exact M10 replay input/result digests and the exact label-manifest digest. Raw consent text, personal identifiers and source documents remain outside M10; the manifest retains only opaque SHA-256 references to externally controlled consent/label records.

### Self-review decision

Do **not** rename these fractions to false-positive/false-negative rates yet. A consented fixture corpus is still not automatically a representative population sample, and the wrong-label denominator is not necessarily the same thing as a statistical negative-class denominator. Stronger terminology requires stronger cohort design.

Tests may mark synthetic fixture shapes as `consented` only to exercise the contract in isolation. That is test data, not real consent evidence, and must never be presented as evaluation results.

## Current controlled synthetic graph result

Production policy — depth 2 / 12 nodes:

- 6 synthetic fixtures;
- 9 labelled admitted pivots: 8 relevant, 1 wrong;
- 11 simulated source attempts;
- 9 successful/yield-producing attempts;
- 2 zero-yield provider failures;
- 11 abstract request-cost units;
- 9 observation-yield units;
- 3 local budget stops.

Candidate depth 3 / 12 nodes:

- 12 labelled admitted pivots: 8 relevant, 4 wrong;
- 14 simulated source attempts;
- 12 successful/yield-producing attempts;
- 2 zero-yield provider failures;
- 14 abstract request-cost units;
- 12 observation-yield units;
- no depth budget stops.

Delta depth 2 → depth 3 in this synthetic cohort: +3 attempts, +3 request-cost units, +3 yield units, +3 wrong-labelled pivots and +0 relevant pivots. This is regression evidence only. Production recursion remains depth 2 / 12 nodes.

## Current controlled M5 sensitivity result

Under `m5-evidence-strength-v1`:

- metadata/temporal: baseline `possible_match`, score 35; omit compatible profile metadata → `insufficient_evidence`, score 20 (`-15`);
- exact identifier: baseline `strong_candidate`, score 75; omit exact confirmed identifier overlap → `insufficient_evidence`, score 20 (`-55`);
- independent cross-link: baseline `strong_candidate`, score 70; omit independent cross-link → `possible_match`, score 35 (`-35`);
- contradiction veto: baseline `contradicted`, score 0; diagnostic omit hard contradiction → `strong_candidate`, score 90 (`+90`).

The contradiction omission is safety-critical diagnostic work only. No M5 factor weight, threshold, veto, calibration status or identity semantic changed.

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

- Next.js UI: `apps/web`
- FastAPI API: `services/api`
- evidence/persistence/normalization: `services/api/app/evidence`
- bounded file intake + review: `services/api/app/uploads`
- governed provider execution: `services/api/app/providers`
- process-wide provider ownership: `services/api/app/providers/shared_runtime.py`
- deterministic correlation: `services/api/app/correlation`
- convergence: `services/api/app/convergence.py`
- typed leads/frontier/source planning/reporting/evaluation: `services/api/app/intelligence`
- M10 cohort aggregation: `services/api/app/intelligence/m10_cohort.py`
- M10 fixture library: `services/api/app/intelligence/m10_fixture_library.py`
- M10 replay identity: `services/api/app/intelligence/m10_replay.py`
- M10 label provenance: `services/api/app/intelligence/m10_label_provenance.py`
- M10 consented accounting: `services/api/app/intelligence/m10_consented_analysis.py`
- M10 factor ablation: `services/api/app/intelligence/m10_factor_ablation.py`, `m10_factor_ablation_execution.py`, `m10_factor_ablation_fixtures.py`
- quick research: `services/api/app/research.py`
- retained cases: `services/api/app/cases.py`

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

Do not reopen V2-D architecture casually. Do not raise production recursion from synthetic evidence, and do not treat the hard-contradiction ablation as a production recommendation.

The next M10 need is **real label evidence, not another synthetic metric**. Assemble a genuinely consented or otherwise independently reviewed cohort whose external evidence records satisfy the PR #109 provenance contract. Every pivot admitted by a scenario must be labelled before the new PR #111 accounting boundary can run.

Do not mark regression fixtures as consented to manufacture progress. Do not call the returned count fractions false-positive/false-negative rates until the cohort design and denominators support that terminology. Production limits stay depth 2 / 12 nodes and M5 remains uncalibrated evidence-strength triage.

A separate acceptable track is fresh review of exactly one zero-spend source candidate from `docs/V2_SOURCE_EXPANSION_PLAN.md`. Gravatar, WebFinger/ActivityPub and RDAP remain candidates, not permissions; current official terms, cost, authentication, fields, contact risk and retention review are required before activation.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
