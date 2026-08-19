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

**Status: multi-kind synthetic cohort, operational accounting, replay identity and ablation manifest established; representative evaluation remains**

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
- replay-anchored M5 factor-ablation manifests that fingerprint the exact current weights, thresholds, independence requirements, strong-factor vocabulary and veto vocabulary.

### Current controlled result

In the broader synthetic cohort, the current depth-2 / 12-node policy admits 9 labelled pivots: **8 relevant and 1 wrong**. It performs 11 simulated source attempts: 9 successful yield-producing attempts and 2 provider failures, for 11 abstract request-cost units and 9 observation-yield units.

A depth-3 / 12-node candidate admits three additional labelled pivots. In these fixtures, **all three additional pivots are wrong-labelled and no additional relevant pivot is gained**. The candidate performs 14 simulated source attempts and therefore adds 3 request-cost units and 3 yield units. Those three additional yield units correspond to the three additional wrong-labelled pivots in this cohort.

This is synthetic fixture evidence, not population evidence or monetary cost. It supports leaving production recursion unchanged; it does not establish an optimal frontier policy or a universal source-efficiency rate.

Replay fingerprints identify the exact controlled experiment definition and result payload. Factor-ablation manifests additionally identify the exact M5 policy and omission scenario set. Neither is an accuracy, calibration, confidence or quality score.

Every omission scenario is diagnostic-only. Removing a veto factor such as `hard_contradiction` is explicitly safety-critical and is not an authorized production-policy candidate.

Still required before increasing recursion or changing correlation thresholds:

- broader consented or otherwise defensibly labelled cohorts;
- execute replay-anchored factor ablations through the real M5 correlation engine rather than a second policy implementation;
- labelled false-positive/false-negative and threshold analysis where defensible labels exist;
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

## Immediate next gate

Do not reopen V2-D architecture casually and do not raise recursion because one fixture family looks favorable.

The preferred next M10 work is **execute the replay-anchored factor-ablation scenarios through the real M5 engine and broaden defensible labels**, not a deeper production graph. The ablation layer must remain diagnostic; it must not fork or reimplement M5 policy. Provider-specific cost weights should be introduced only when a real adapter needs more fidelity than one abstract request-cost unit per simulated call.

A separate acceptable track is fresh review of exactly one additional zero-spend source candidate from `docs/V2_SOURCE_EXPANSION_PLAN.md`. Gravatar, WebFinger/ActivityPub and RDAP remain candidates, not permissions. Current official terms, cost, authentication, returned fields, contact risk and retention implications must be reviewed before activation.

Production recursion remains **depth 2 / 12 nodes**. M10 evidence, not feature pressure, decides whether those limits change.

Success means the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
