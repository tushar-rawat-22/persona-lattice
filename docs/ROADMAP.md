# Roadmap

PersonaLattice is a private, evidence-first research workbench. The public route is a demo surface; real intake, provider execution and retained case data belong to one authenticated operator account unless a future security/privacy review changes that model.

## Permanent product rules

- Observations, factual Claims and correlation results remain separate.
- Every lead and conclusion keeps provenance.
- A lead is a research direction, not proof of identity.
- Same-handle reuse alone remains insufficient evidence.
- M5 remains uncalibrated evidence-strength triage, not identity probability.
- Contradictions/vetoes and stale evidence remain visible.
- No AI/ML/embedding/biometric identity decision is authorized by the current roadmap.
- No private-account bypass, credential/account-recovery enumeration, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking or regulated eligibility decisioning is a product capability.
- The default product must remain usable without paid APIs, paid hosting, paid databases, paid proxies or paid enrichment.

## M0-M6 — core platform

**Status: complete**

The repository, evidence model, normalization/provenance layer, bounded file intake, governed provider framework, Sherlock discovery, deterministic M5 correlation and local evidence dashboard are implemented and covered by CI.

M5 permanent outputs remain:

- `calibration_status=uncalibrated`
- `is_identity_claim=false`

## M7 — private one-admin live research product

**Status: implemented and manually accepted locally**

Implemented:

- one deployment-configured admin identity;
- Argon2 password verification;
- opaque HttpOnly sessions, logout/revocation and CSRF protection;
- public demo route separated from private `/admin`;
- same-origin Next.js `/api` proxy;
- authenticated real intake/research;
- reviewed Sherlock plus GitHub, GitLab and Codeforces public-profile enrichment;
- phone numbering-plan/carrier/region/time-zone metadata;
- public DNS infrastructure metadata;
- optional exact public-web search when configured;
- retained private cases.

Manual acceptance has succeeded through a local public HTTPS tunnel. That proves the private operator path but is not durable hosting.

## M8 — privacy lifecycle and operations

**Status: substantially implemented**

Implemented:

- automatic expiry purge and explicit delete workflows;
- privacy-safe audit events;
- 30-day default retained-case lifecycle;
- secrets outside Git;
- bounded source/resource budgets.

Remaining operational work:

- prefer local/self-hosted operation unless durable free hosting materially improves the workflow;
- define backup/restore after a persistent production store actually exists;
- measure provider behavior before considering any optional metered enrichment.

## M9 — evidence graph and report convergence

**Status: private V1 implemented; V2 architecture extends it**

Private V1 admits live provider evidence into an ephemeral canonical M1 graph, runs M5 and retains only bounded report/provenance records. It deliberately avoids a second persistent raw-personal-data graph.

### V2-A — typed recursive evidence lead graph

**Status: complete — PR #20**

Implemented exact-field lead extraction, typed lead kinds/dispositions, M1-consistent normalization and fail-closed handling for sensitive field classes.

### V2-B — deterministic frontier orchestration

**Status: complete — PR #21**

Implemented reservation-safe frontier scheduling, duplicate/cycle suppression, reason-coded outcomes and additive lead-graph report state.

Current hard ceilings remain **depth 2 / 12 nodes**. Raising them is an evaluation decision, not a feature checkbox.

### V2-C — source capability registry and planner

**Status: complete — PR #22**

Capability, execution authority, lifecycle state, cost class, credential class, source-policy review and recursive eligibility are now explicit. Planned sources remain non-executable by construction.

### V2-D — source-adapter/runtime consistency and architecture closure

**Status: active; most runtime/source-state work complete**

Completed provider/runtime work:

- PR #24: catalog-to-runtime source binding admission;
- PR #25: storage-independent `ProviderRuntime`;
- PR #26: Sherlock quick research on the governed runtime;
- PR #27/#28: GitHub migration plus rate-policy repair;
- PR #29: one process-wide production runtime;
- PR #30: GitLab runtime migration;
- PR #31: Codeforces runtime migration;
- PR #32: public DNS runtime migration.

Completed source-state/report/evaluation work:

- PR #34: typed source-run state/reason contract;
- PR #35: deterministic privacy-bounded source-run projection;
- PR #36: explicit execution outcome mapping;
- PR #37: converged node source-run projection;
- PR #38: normal quick research emits factual source-run records;
- PR #40: deterministic aggregate/per-source evaluation counters;
- PR #42: deterministic full-vocabulary source evaluation fixture matrix.

The source-run path does not infer provider contact from warning strings. An optional source that was never configured is not a negative result. A local pre-call budget stop is not a provider failure. A completed `not_found` call is a valid completed lookup.

PR #40 deliberately adds **counts, not reliability percentages**. Current evaluation records attempts, completed attempts, attempted failures, result-bearing records, no-match results, observation yield, remote rate limits, execution failures, local budget stops, optional-unconfigured states and scheduler/review/display/blocked states. Sample size remains visible globally and per source.

PR #42 locks every current source-run state and reason into one deterministic synthetic matrix. If the vocabulary changes later, evaluation semantics must be reviewed and the matrix updated instead of silently accepting the new state.

Remaining before V2-D closes:

1. add graph-growth/wrong-pivot/duplicate measurements over deterministic graph fixtures;
2. add explicit typed pre-execution/configuration/malformed-result outcomes only where the runtime can prove them;
3. migrate the existing optional Brave exact-match path behind `ProviderRuntime` while preserving no-key zero-spend operation and without expanding source coverage;
4. remove the final legacy network execution allowance;
5. finish document-candidate-to-reviewed-lead plumbing;
6. expose source-state/evaluation summaries cleanly to the operator;
7. run final architecture consistency evaluation before activating new network providers.

No new third-party source should be activated during these closure blocks.

## M10 — evaluation and calibration laboratory

**Status: deterministic source-failure fixture layer established; graph evaluation remains**

Required before increasing recursion limits or changing correlation thresholds:

- deterministic full-vocabulary source failure/state fixture matrix;
- wrong-pivot and duplicate measurements;
- graph-growth measurements;
- provider attempt/failure/no-match/yield counts with explicit denominators;
- deterministic replay/factor ablations;
- labelled false-positive/false-negative and threshold analysis where a defensible labelled set exists;
- no probability claim unless calibration evidence supports it.

Observation count is evidence yield, not evidence quality. Provider percentages should not be published until sample-size and denominator semantics are controlled.

## Immediate next gate

Add deterministic graph-growth, duplicate and wrong-pivot measurements before changing recursion limits. After that, finish the remaining existing-source migration and document-to-reviewed-lead plumbing.

Only after V2-D architecture closure may new public/API sources be reviewed one at a time. Each activation must re-check current official terms, authentication, limits and cost from primary sources; old pricing or quota notes are not authority.

Success means a small clue can grow into a broad evidence graph while the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
