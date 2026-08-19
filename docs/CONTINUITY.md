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
- Main before PR #109: `53a0ccd799c274008b53e0d15eeb4c8821d9c894`
- PR #109: replay-anchored M10 label provenance manifest
- Exact tested implementation/docs head: `59863bcf4da633c31fd953aebd19a7fe583b84cd`
- Exact-head CI: run `32219724164`, full success across API 3.11/3.13, dependency checks/audits, Ruff, web audit/lint/typecheck/build and production API image
- PR #109 merge: `8faf6ca5d191fcede1d6ae2102104408bf092d08`
- ADR: `docs/decisions/0062-m10-label-provenance-manifest.md`
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
- Post-V2-D source expansion: Bluesky public profiles are active for valid AT handles through the governed runtime, PR #98 / ADR 0055.
- M10 now has source-state fixtures, graph-limit comparison, multi-kind synthetic cohort support, source-attempt/yield/request-cost accounting, deterministic graph replay, replay/policy-anchored factor ablations through the real `CorrelationEngine`, UUID-independent controlled M5 fixture/result replay, and explicit replay-anchored label provenance. Representative consented evaluation and threshold/error analysis remain incomplete.

## Latest block — M10 label provenance before error analysis

PR #109 closes a provenance gap that remained after deterministic replay was established. Reproducible synthetic labels are useful regression data, but they are not consented ground truth and must not silently become population denominators.

New module: `services/api/app/intelligence/m10_label_provenance.py`.

The new contract:

- defines `M10LabelBasis.SYNTHETIC` and `M10LabelBasis.CONSENTED`;
- requires exactly one `M10FixtureLabelProvenance` record for every fixture in the replayed cohort;
- stores only fixture name, label basis and an opaque lowercase SHA-256 reference to an external label/consent record;
- does not store raw consent text, source documents or personal identifiers in the M10 manifest;
- rebuilds the exact M10 replay from the supplied fixtures and fails closed if either replay input or result digest drifts;
- rejects duplicate, missing or extra provenance records;
- fingerprints replay identity, provenance basis, evidence-record digest and exact fixture pivot labels;
- keeps synthetic and consented declared-label corpus counts separate;
- returns counts only and does not calculate error rates, confidence, probability or calibration.

A self-review flaw was corrected before merge: the first version named all fixture labels as a denominator-like `labelled_pivot_count`. That was misleading because a frontier scenario may never admit every labelled pivot. The final API uses `declared_*` label counts. Scenario-specific admitted denominators continue to come from actual graph evaluation counters.

The evidence digest is only an opaque external-record reference. It must not be a bare hash of a personal identifier; the underlying label/consent evidence remains outside this public-safe manifest and under the appropriate data-handling controls.

## Current controlled graph M10 result

Current production policy — depth 2 / 12 nodes:

- 6 synthetic fixtures;
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

This remains synthetic fixture evidence, not population evidence or monetary cost. Production recursion stays unchanged.

## Current controlled M5 sensitivity result

Under `m5-evidence-strength-v1`:

- `possible_metadata_temporal`: baseline `possible_match`, score 35; omit compatible profile metadata → `insufficient_evidence`, score 20, delta `-15`;
- `strong_exact_identifier`: baseline `strong_candidate`, score 75; omit exact confirmed identifier overlap → `insufficient_evidence`, score 20, delta `-55`;
- `strong_independent_cross_link`: baseline `strong_candidate`, score 70; omit independent cross-link → `possible_match`, score 35, delta `-35`;
- `contradiction_veto`: baseline `contradicted`, score 0; diagnostic omit hard contradiction → `strong_candidate`, score 90, delta `+90`.

The contradiction omission is safety-critical diagnostic work only. No M5 weight, threshold, veto, calibration status or identity semantic changed.

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
- governed provider execution: `services/api/app/providers`
- process-wide provider ownership: `services/api/app/providers/shared_runtime.py`
- deterministic correlation: `services/api/app/correlation`
- convergence: `services/api/app/convergence.py`
- typed leads/frontier/source planning/reporting/evaluation: `services/api/app/intelligence`
- M10 cohort aggregation: `services/api/app/intelligence/m10_cohort.py`
- M10 multi-kind fixture library: `services/api/app/intelligence/m10_fixture_library.py`
- M10 graph replay identity: `services/api/app/intelligence/m10_replay.py`
- M10 label provenance: `services/api/app/intelligence/m10_label_provenance.py`
- M10 factor-ablation identity/execution: `services/api/app/intelligence/m10_factor_ablation.py`, `m10_factor_ablation_execution.py`
- M10 UUID-independent controlled ablation fixtures/replay: `services/api/app/intelligence/m10_factor_ablation_fixtures.py`
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

Do not reopen V2-D architecture casually. Do not raise production recursion from the current synthetic evidence, and do not treat the safety-critical hard-contradiction ablation as a production recommendation.

M10 now has an explicit provenance boundary for labelled graph fixtures. The preferred next work is to add a genuinely consented or separately reviewed labelled cohort that can satisfy this manifest contract, then implement false-positive/false-negative or threshold analysis only where the actual admitted labels and denominators support it. Do not reinterpret the existing synthetic six-fixture corpus as consented evidence.

A separate acceptable track remains fresh review of exactly one zero-spend source candidate from `docs/V2_SOURCE_EXPANSION_PLAN.md`. Gravatar, WebFinger/ActivityPub and RDAP remain candidates, not permissions; current official terms, cost, authentication, fields, contact risk and retention review are required before activation.

Production limits remain depth 2 / 12 nodes. M5 remains uncalibrated evidence-strength triage, not identity probability.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
