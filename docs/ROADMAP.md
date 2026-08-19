# Roadmap

PersonaLattice is a private, evidence-first research workbench. The public route is a demo surface. Real intake, provider execution and retained case data belong to one authenticated operator account unless a future security/privacy review changes that model.

## Product rules

- Observations, factual claims and correlation results stay separate.
- Every lead and conclusion keeps provenance.
- A lead is a research direction, not proof of identity.
- Same-handle reuse alone is weak evidence.
- M5 remains uncalibrated evidence-strength triage, not identity probability.
- Contradictions, vetoes and stale evidence remain visible.
- No biometric/embedding/ML identity decision is authorized.
- No private-account bypass, credential/account-recovery probing, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking or regulated eligibility decisioning is a product capability.
- The required operating baseline stays free: no paid API, hosting, database, proxy or enrichment dependency.

## Core platform — M0 through M6

**Complete.**

Repository/CI, evidence and provenance storage, deterministic normalization, bounded file intake, the governed provider framework, reviewed Sherlock discovery, deterministic M5 correlation and the local evidence dashboard are implemented.

M5 permanent outputs remain `calibration_status=uncalibrated` and `is_identity_claim=false`.

## Private operator product — M7 through M9

**Implemented; local one-admin flow manually accepted.**

The private product has one deployment-configured admin, Argon2 password verification, HttpOnly sessions, CSRF protection, a private `/admin` route, same-origin API proxying, retained cases, expiry/delete controls and bounded live research.

Current live sources:

- reviewed Sherlock username discovery;
- GitHub, GitLab and Codeforces public profiles;
- Bluesky public profiles for valid AT handles;
- phone numbering-plan metadata;
- public DNS infrastructure metadata;
- authoritative metadata-only RDAP for explicit domain seeds;
- optional Brave exact public-web search when configured.

Local operation is the zero-spend baseline. The paid Render topology remains an optional reference at `deploy/render-paid.yaml`.

Privacy/operations include a 30-day default retained-case lifecycle, automatic expiry purge, explicit deletion, privacy-safe audit events, secrets outside Git and bounded request/concurrency/timeout/response limits. Backup/restore remains deferred until a persistent hosted production store is chosen.

## Recursive evidence graph — V2

### V2-A — typed lead graph

**Complete — PR #20.** Typed lead kinds/dispositions, exact-field extraction, M1-consistent normalization and fail-closed handling for sensitive fields.

### V2-B — deterministic frontier

**Complete — PR #21.** Reservation-safe scheduling, duplicate/cycle suppression, reason-coded outcomes and retained graph state.

Production limits remain **depth 2 / 12 nodes**. Raising them requires evaluation evidence.

### V2-C — source capability registry

**Complete — PR #22.** Capability, execution authority, lifecycle state, cost class, credential class, source-policy review and recursive eligibility are explicit. Planned sources remain non-executable by construction.

### V2-D — runtime consistency and architecture closure

**Complete — PRs #89-#90.** Every executable network source is behind the governed runtime. Catalog, binding, provider registry and process runtime ownership are checked symmetrically. Required active recursive sources must remain zero-spend eligible; non-zero-spend recursive sources can only be optional.

Source-run accounting is phase-proven, retained evidence/provenance has canonical owners, historical retained formats remain read-only compatible, and the reviewed-document chain is server-owned from extraction through explicit case execution.

## Source expansion

New sources must use the existing catalog → binding → provider registry → process-wide `ProviderRuntime` → typed source-run → canonical evidence path.

### Bluesky

**Active — PR #98.** Credentialless and zero-direct-cost. Only valid AT handles are applicable. Retained fields are limited to DID, normalized handle and optional display name plus non-identity/public-visibility metadata. Public-web opt-out and suspended/deactivated accounts are neutral attempted `withheld` outcomes.

### RDAP

**Active — PR #137.** Credentialless, zero-direct-cost registration metadata for explicit DOMAIN seeds. The source emits no recursive subject leads. Registrant/registrar/contact names, organizations, addresses, email addresses and telephone numbers are excluded from admitted observations.

The live path uses IANA longest-match bootstrap routing, one process-wide bootstrap cache, fresh DNS/global-address checks, IP-pinned HTTPS with hostname TLS validation, bounded redirects/response size and separate validation of canonical query URL versus final evidence locator.

`routing_unavailable` remains a non-attempt outcome when prerequisite routing authority is unavailable. Once an authoritative RDAP provider is contacted, rate limits, transient failures and malformed results use attempted-failure semantics. Discovered domain clues remain **display-only**; only explicit DOMAIN seeds run RDAP.

No WHOIS fallback, RDRS/nonpublic workflow, reverse/bulk lookup or contact harvesting is approved.

### Gravatar

**Planned.** Admission preflight exists, but activation remains blocked by provider privacy-policy requirements and the need for a free server-side key outside Git. It must remain unnecessary to the zero-spend baseline.

### WebFinger

**Planned.** Parser/admission, SSRF-safe transport, URL-only semantics and an exact-host policy gate exist. The production host-approval registry remains empty because no reviewed host has yet met the required current terms/privacy basis. ActivityPub actor fetching is separate and unapproved.

## M10 — evaluation and calibration laboratory

**Infrastructure established; representative evidence remains the bottleneck.**

Implemented:

- deterministic source-state/failure fixtures;
- provider attempt/failure/no-match/yield counters with explicit denominators;
- graph growth, depth, duplicate and budget-stop counters;
- label-gated wrong-pivot measurement;
- controlled graph-limit comparison through the production `LeadFrontier`;
- a six-fixture synthetic cohort spanning username, email, URL and reviewed-phone seeds;
- provider-boundary request-cost and observation-yield accounting;
- replay fingerprints for exact cohort inputs/results;
- replay-anchored real-engine M5 factor ablations;
- rollback-only diagnostic M5 execution;
- UUID-independent semantic fixture/result fingerprints;
- explicit label-provenance manifests;
- consented-only scenario accounting with exact numerator/denominator counts;
- a bounded local consented-cohort runner so private consented identifiers do not need to become repository fixtures;
- an explicit **independently reviewed** label basis and reviewed-only accounting boundary, kept separate from consent and synthetic regression data.

M10 now distinguishes three provenance bases: `synthetic`, `consented` and `independently_reviewed`. None can silently satisfy another basis. Both consented-only and reviewed-only analysis require complete labels for admitted pivots and report exact corpus counts/fractions rather than unsupported population rates.

The reviewed path stores only an opaque SHA-256 reference to an external review record. It does not put raw review notes, personal identifiers or source documents into the experiment manifest.

### Current synthetic graph result

Production depth 2 / 12 nodes admits 9 labelled pivots: **8 relevant, 1 wrong**, with 11 simulated source attempts.

The depth-3 / 12-node diagnostic candidate admits 12 labelled pivots: **8 relevant, 4 wrong**, with 14 simulated attempts.

In this synthetic cohort, the extra depth adds three attempts and three wrong-labelled pivots with no additional relevant pivot. This is regression evidence, not population evidence. Production stays depth 2 / 12 nodes.

### Current M5 ablation result

- compatible profile metadata omission: `possible_match` 35 → `insufficient_evidence` 20;
- exact confirmed identifier omission: `strong_candidate` 75 → `insufficient_evidence` 20;
- independent cross-link omission: `strong_candidate` 70 → `possible_match` 35;
- diagnostic hard-contradiction omission: `contradicted` 0 → `strong_candidate` 90.

The contradiction omission is safety-critical diagnostic work only. Production factor weights, thresholds and vetoes are unchanged.

### Remaining M10 gate

The bottleneck is real evidence, not another synthetic metric.

Use the consented path only when genuine consent records support the labels. Use the independently reviewed path only when a real external review record supports the labels. Do not manufacture either basis from repository fixtures or a bare hash of an identifier.

Do not publish false-positive/false-negative, calibration, probability or population-performance claims until cohort design and denominators genuinely support those terms.

## Immediate next gate

1. Put this reviewed-label boundary through exact-head CI and merge only if the existing consented path remains strict and unchanged.
2. When lawful real evidence exists, run a genuinely consented or independently reviewed cohort through the matching boundary; do not upgrade one provenance basis into another.
3. Add another external source only if it materially improves coverage and its current terms, privacy, authentication, provenance and zero-spend status are defensible.
4. Keep production recursion at depth 2 / 12 nodes and keep `hard_contradiction` as a production veto.
5. Continue improving the operator workflow around evidence/provenance hierarchy rather than generic AI-SaaS presentation patterns.

Success means the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
