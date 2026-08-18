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

M5 permanent outputs remain:

- `calibration_status=uncalibrated`
- `is_identity_claim=false`

## M7 — private one-admin research product

**Status: implemented and manually accepted locally**

The private product has one deployment-configured admin, Argon2 password verification, HttpOnly sessions, CSRF protection, a private `/admin` route, same-origin API proxying, retained cases, delete/expiry controls and live bounded research.

Current live research sources include reviewed Sherlock, GitHub, GitLab, Codeforces, phone numbering-plan metadata and public DNS infrastructure metadata. Brave exact public-web search is optional when configured.

Local HTTPS-tunnel acceptance proves the operator path. It is not a requirement to buy durable hosting; local/self-hosted operation remains the zero-spend baseline.

## M8 — privacy lifecycle and operations

**Status: substantially implemented**

Implemented:

- 30-day default retained-case lifecycle;
- automatic expiry purge and explicit deletion;
- privacy-safe audit events;
- secrets outside Git;
- bounded request, concurrency, timeout and response limits.

Remaining operational work is limited to backup/restore design if a persistent production store is introduced, plus provider behavior measurement before any optional metered dependency is treated as operationally important.

## M9 — evidence graph and report convergence

**Status: private V1 implemented; V2 architecture extends it**

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

**Status: implementation complete enough for final closure audit**

Every currently executable network source is behind the governed runtime. The executable legacy network allowance is empty. Brave remains optional/metered; without `BRAVE_SEARCH_API_KEY` it is not attempted and the zero-spend path remains usable.

Source-run accounting is phase-proven. Policy/configuration/local-budget stops are non-attempts; completed zero-result calls are `not_found`; remote failures and malformed returned results count as attempts only when that phase is mechanically known. Generic phase-ambiguous validation remains unclassified rather than being guessed into failure metrics.

PR #85 closed the retained-report consistency gap: quick retained cases persist the same typed source-run projection used by converged nodes, and that projection carries deterministic source-evaluation counters derived from the same records. The projection remains metadata-only and does not copy identifier values, source locators, provider payloads, credentials, exception text or timing data. Historical cases are not backfilled with guessed source state. ADR 0048 records the decision.

PR #87 closed the corresponding private operator visibility gap. Reviewed-upload cases show retained `seed_provenance`; quick cases show their top-level retained source-run state/evaluation projection; converged cases show the same projection per research node. Historical cases that predate typed source-run retention show source execution state as unavailable. The browser consumes retained state/reason/attempt/counter fields directly and does not parse warnings or reimplement provider policy. ADR 0049 records the decision.

Retained-report ownership has been tightened across PRs #70, #72, #74, #77 and #79. Complete provider evidence and provenance have canonical retained owners; connected fields, M5 candidates and converged edges use validated references rather than copying values/locators into parallel structures. PR #81 moved those reference resolutions into the private UI and removed temporary server-side response hydration for new retained formats while keeping explicit read-only compatibility for historical self-contained cases.

The reviewed-document chain is complete:

- PR #56: deterministic candidate spans and fail-closed reviewed identifier promotion;
- PR #58: PDF page-span provenance and corrected flattened-text limits;
- PR #60: short-lived server-owned review state without raw-document retention;
- PR #62/#63: atomic confirm/reject/re-review/promotion with immutable candidate value/provenance;
- PR #64: authenticated, CSRF-protected HTTP review actions;
- PR #66: separate explicit retained-case execution from a currently confirmed, research-authorized server-owned candidate;
- PR #83: private operator controls for confirm/reject/re-review/promotion preview and separate explicit converged-case execution;
- PR #87: reviewed-document seed provenance and source execution/evaluation state are visible in retained private cases without moving authorization into the browser.

Cross-layer closure guards from PR #68 keep catalog, binding, registry and process-wide runtime ownership aligned and enforce the zero-spend baseline for required recursive sources.

## M10 — evaluation and calibration laboratory

**Status: deterministic evaluation contracts established; representative labelled evaluation remains**

Established:

- complete deterministic source-state/failure fixture coverage;
- provider attempt/failure/no-match/yield counters with explicit denominators;
- graph growth, depth, duplicate and budget-stop counters;
- label-gated wrong-pivot measurement;
- controlled graph-limit comparison through the production frontier policy.

Still required before increasing recursion or changing correlation thresholds:

- multiple defensible synthetic/consented labelled fixture families;
- deterministic replay/factor ablations;
- labelled false-positive/false-negative and threshold analysis where defensible labels exist;
- provider cost/yield implications for larger frontier policies;
- no probability claim unless calibration evidence supports it.

Observation count is evidence yield, not evidence quality. Reliability percentages should not be published without controlled sample size and denominator semantics.

## Immediate next gate

Run the final V2-D closure audit. Do not add another provider during the audit.

The audit must prove that these layers still agree and fail closed together:

1. source catalog, executable bindings, provider registry and process-wide runtime ownership;
2. retained-report ownership, canonical provenance references and read-only historical compatibility;
3. upload candidate review → promotion → separate explicit case execution authority;
4. typed source-state/evaluation semantics and private UI consumption without warning inference;
5. required zero-spend operation, with optional/metered Brave remaining non-required;
6. roadmap, ADR and continuity documentation matching executable behavior and verified CI.

If no material gap remains, record V2-D as closed before reviewing or activating any new third-party API/source. If the audit finds a real inconsistency, fix that inconsistency first rather than closing the milestone administratively.

Production recursion remains depth 2 / 12 nodes.

Success means the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
