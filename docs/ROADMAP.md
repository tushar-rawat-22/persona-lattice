# Roadmap

PersonaLattice is a private, evidence-first research workbench. The public route is a demo surface; real intake, provider execution and retained case data belong to one authenticated operator account unless a future security/privacy review changes that model.

## Permanent product rules

- Observations, factual Claims and correlation results remain separate.
- Every lead and conclusion keeps provenance.
- A lead is a research direction, not proof of identity.
- Same-handle reuse alone remains insufficient evidence.
- M5 remains uncalibrated evidence-strength triage, not identity probability.
- Contradictions, vetoes and stale evidence remain visible.
- No AI/ML/embedding/biometric identity decision is authorized by the current roadmap.
- No private-account bypass, credential/account-recovery enumeration, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking or regulated eligibility decisioning is a product capability.
- The default product must remain usable without paid APIs, paid hosting, paid databases, paid proxies or paid enrichment.

## M0-M6 — core platform

**Status: complete**

Repository and CI, evidence/provenance model, normalization, bounded file intake, governed provider framework, reviewed Sherlock discovery, deterministic M5 correlation and the local evidence dashboard are implemented.

M5 permanent outputs remain `calibration_status=uncalibrated` and `is_identity_claim=false`.

## M7 — private one-admin research product

**Status: implemented and manually accepted locally**

The private product has one deployment-configured admin, Argon2 password verification, HttpOnly sessions, CSRF protection, a private `/admin` route, same-origin API proxying, retained cases, delete/expiry controls and live bounded research.

Current live research sources include reviewed Sherlock, GitHub, GitLab, Codeforces, Bluesky public profiles for valid AT handles, phone numbering-plan metadata and public DNS infrastructure metadata. Brave exact public-web search is optional when configured.

Local operation is the zero-spend baseline. Paid hosting is optional; the previously reviewed Render topology is retained only at `deploy/render-paid.yaml`.

## M8 — privacy lifecycle and operations

**Status: substantially implemented**

Implemented: 30-day default retained-case lifecycle, automatic expiry purge, explicit deletion, privacy-safe audit events, secrets outside Git, and bounded request/concurrency/timeout/response limits.

Backup/restore design remains deferred until a persistent hosted production store is actually selected.

## M9 — evidence graph and report convergence

**Status: implemented**

Private V1 admits live provider observations into an ephemeral canonical M1 graph, runs M5 and retains bounded report/provenance records. It does not create a second persistent raw-personal-data graph.

### V2-A — typed recursive evidence lead graph

**Status: complete — PR #20**

Exact-field lead extraction, typed lead kinds/dispositions, M1-consistent normalization and fail-closed handling for sensitive field classes.

### V2-B — deterministic frontier orchestration

**Status: complete — PR #21**

Reservation-safe scheduling, duplicate/cycle suppression, reason-coded outcomes and additive lead-graph report state.

Production limits remain **depth 2 / 12 nodes**. Raising them requires evaluation evidence.

### V2-C — source capability registry and planner

**Status: complete — PR #22**

Capability, execution authority, lifecycle state, cost class, credential class, source-policy review and recursive eligibility are explicit. Planned sources remain non-executable by construction.

### V2-D — runtime consistency and architecture closure

**Status: complete — PRs #89-#90**

Every executable network source is behind the governed runtime. The executable legacy-network allowance is empty. Catalog, binding, provider registry and process runtime ownership are checked symmetrically. Required active recursive sources must remain zero-spend eligible; non-zero-spend recursive sources can only be optional.

Source-run accounting is phase-proven, retained evidence/provenance has canonical owners, historical retained formats remain read-only compatible, and the reviewed-document chain is server-owned from extraction through explicit case execution.

The default operating contract is `docs/ZERO_SPEND_RUNBOOK.md`; paid Render deployment is an optional reference at `deploy/render-paid.yaml`.

V2-D closure does not authorize larger recursion, wider retention, paid baseline dependencies or identity-probability claims.

## M10 — evaluation and calibration laboratory

**Status: deterministic replay, real-engine ablation, label provenance and consented-scenario accounting infrastructure established; representative evaluation remains**

Established:

- complete deterministic source-state/failure fixture coverage;
- provider attempt/failure/no-match/yield counters with explicit denominators;
- graph growth, depth, duplicate and budget-stop counters;
- label-gated wrong-pivot measurement;
- controlled graph-limit comparison through the production `LeadFrontier`;
- count-only cohort aggregation without reliability/probability claims;
- a reusable six-fixture synthetic cohort spanning username, email, URL and reviewed-phone seeds;
- aggregate review-required, display-only and blocked policy-state counts;
- provider-boundary source-attempt, successful/zero-yield attempt, observation-yield-unit and abstract request-cost-unit accounting;
- versioned SHA-256 replay fingerprints for exact canonicalized cohort inputs and deterministic comparison results;
- replay-anchored M5 factor-ablation manifests that fingerprint the exact current weights, thresholds, independence requirements, strong-factor vocabulary and veto vocabulary;
- controlled factor omissions executed through the production `CorrelationEngine`, with baseline/ablated outcome, score and independence-group deltas;
- non-retaining M10 correlation execution: diagnostic M5 runs are rolled back and do not become retained case evidence;
- a versioned reusable semantic specification for controlled M5 ablation cases, with UUID-independent fixture, per-case and result replay fingerprints;
- a replay-anchored label-provenance manifest that requires explicit `synthetic` or `consented` basis and an opaque SHA-256 external-record reference for every labelled graph fixture;
- separate synthetic and consented **declared-label corpus counts**, deliberately distinct from scenario-specific admitted-pivot denominators;
- a consented-only scenario-accounting boundary that rejects synthetic/mixed cohorts and unlabelled admitted pivots, records exact admitted/missed label counts, and exposes numerator/denominator count fractions without converting them into population error rates.

### Current controlled graph result

In the broader synthetic cohort, the current depth-2 / 12-node policy admits 9 labelled pivots: **8 relevant and 1 wrong**. It performs 11 simulated source attempts: 9 successful yield-producing attempts and 2 provider failures, for 11 abstract request-cost units and 9 observation-yield units.

A depth-3 / 12-node candidate admits three additional labelled pivots. In these fixtures, **all three additional pivots are wrong-labelled and no additional relevant pivot is gained**. The candidate performs 14 simulated source attempts and therefore adds 3 request-cost units and 3 yield units.

This is synthetic fixture evidence, not population evidence or monetary cost. It supports leaving production recursion unchanged; it does not establish an optimal frontier policy or a universal source-efficiency rate.

### Current controlled M5 ablation result

The current real-engine controlled cases remain:

- metadata/temporal: baseline `possible_match`, score 35; omit compatible profile metadata → `insufficient_evidence`, score 20 (`-15`);
- exact identifier: baseline `strong_candidate`, score 75; omit exact confirmed identifier overlap → `insufficient_evidence`, score 20 (`-55`);
- independent cross-link: baseline `strong_candidate`, score 70; omit independent cross-link → `possible_match`, score 35 (`-35`);
- contradiction veto: baseline `contradicted`, score 0; diagnostic omit `hard_contradiction` → `strong_candidate`, score 90 (`+90`).

The contradiction omission is safety-critical diagnostic work only. These controlled deltas are not calibration evidence, population error rates or permission to change production policy.

### Label provenance and consented-scenario boundary

Reproducible labels are not automatically defensible ground truth. PR #109 / ADR 0062 adds an explicit provenance layer before future error-style work.

Each labelled fixture must have a matching provenance record whose basis is `synthetic` or `consented`, plus an opaque SHA-256 reference to the external label/consent record. The manifest is bound to the exact M10 replay input and result digests and fails closed if the cohort, labels or provenance coverage drift.

The manifest exposes **declared** label corpus counts. It does not treat every fixture label as an admitted-pivot denominator because a frontier policy may never execute or admit that labelled pivot.

PR #111 / ADR 0063 adds the next boundary: consented scenario accounting refuses synthetic or mixed provenance and refuses any scenario with unlabelled admitted pivots. For an eligible cohort it records exact admitted relevant/wrong counts, relevant/wrong labels not admitted by each scenario, and exact count fractions for admitted-wrong share and relevant-label recall. Fractions remain numerator/denominator pairs; they are not published as population false-positive/false-negative rates, confidence, calibration or identity probability.

Raw consent text and personal identifiers do not belong in either manifest or analysis record. The evidence-record digest must not be a bare hash of a personal identifier.

Still required before increasing recursion or changing correlation thresholds:

- a genuinely consented or separately reviewed labelled cohort large enough to support defensible analysis;
- run that cohort through the consented-only accounting boundary with complete admitted-pivot labels;
- stronger false-positive/false-negative or threshold terminology only if the cohort definition and denominators actually justify it;
- provider-specific request/yield weights only where a real adapter needs more than the current one-request/one-yield fixture abstraction;
- reviewed monetary pricing only when an actual provider has a current price model relevant to a decision;
- no probability claim unless calibration evidence supports it.

Observation/yield count is evidence volume, not evidence quality. Reliability percentages should not be published without controlled sample size and denominator semantics.

## Reviewed source expansion

V2-D is closed. New sources use the existing catalog → binding → provider registry → process-wide `ProviderRuntime` → typed source-run → canonical evidence path rather than adding parallel execution branches.

### Bluesky public profiles

**Status: active — PR #98**

Bluesky is credentialless and zero-direct-cost. Applicability is narrower than generic username research: only normalized values that pass the AT-handle admission contract can trigger a request. Plain usernames and malformed/`@` UI forms are skipped before provider execution.

Retained fields stay minimal: DID, normalized handle and optional display name plus account-candidate/non-identity/public-visibility flags. Public-web opt-out and suspended/deactivated accounts remain neutral attempted `withheld` outcomes rather than `not_found` or provider failure.

The first rollout remains sequential after the existing public-profile enrichment block. Optimize only from measured latency/yield evidence.

### WebFinger

**Status: pre-activation transport boundary complete — PRs #115 and #117**

PR #115 established the network-free RFC 7033 admission contract for explicit HTTPS profile URLs and bounded JRD links. PR #117 adds the redirect/DNS SSRF transport needed before activation.

The transport resolves every request and redirect host immediately before I/O, independently rejects malformed/non-global resolver output, pins TCP to the admitted IP while validating TLS against the DNS hostname, and re-runs the same admission process on every redirect. Redirects are bounded to three. There is no HTTP downgrade and no new runtime dependency.

WebFinger is still **PLANNED, unbound and non-recursive**. ActivityPub actor fetching remains outside this reviewed capability.

The remaining activation blocker is the catalog/output mismatch: the planned `webfinger_activitypub` declaration still claims URL + generic USERNAME + NAME output, while the reviewed WebFinger boundary supports URL-only output. That contract must be corrected before an atomic provider activation.

## Immediate next gate

Do not reopen V2-D architecture casually, do not remove safety-critical M5 vetoes because an ablation changes the score, and do not raise recursion because one fixture family looks favorable.

M10 now has both label-provenance and consented-only scenario-accounting boundaries. The preferred evaluation work is therefore **not another synthetic metric**: assemble a genuinely consented or otherwise separately reviewed labelled cohort whose external evidence records satisfy the existing provenance contract, then run it through the consented analysis with complete admitted-pivot labels. Do not mark test fixtures as consented merely to obtain fractions.

Only after that evidence exists should PersonaLattice decide whether stronger false-positive/false-negative or threshold analysis is mathematically justified. The existing six-fixture synthetic cohort remains diagnostic regression data.

For source expansion, WebFinger's admission and SSRF-safe transport boundaries are now in place, but activation still requires the URL-only catalog correction plus one atomic provider/binding/registry/shared-runtime/quick-research/typed-state integration. Gravatar remains blocked on its privacy-policy requirement. RDAP remains an acceptable parallel zero-spend source-review track.

Production recursion remains **depth 2 / 12 nodes**. M10 evidence, not feature pressure, decides whether those limits change. M5 remains uncalibrated evidence-strength triage and `hard_contradiction` remains a production veto.

Success means the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
