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

Local HTTPS-tunnel acceptance proves the operator path. Local operation is the zero-spend baseline; paid hosting is optional and not required for the product to work. The previously reviewed paid Render topology is retained only at `deploy/render-paid.yaml`.

## M8 — privacy lifecycle and operations

**Status: substantially implemented**

Implemented:

- 30-day default retained-case lifecycle;
- automatic expiry purge and explicit deletion;
- privacy-safe audit events;
- secrets outside Git;
- bounded request, concurrency, timeout and response limits.

Remaining operational work is limited to backup/restore design if a persistent hosted production store is introduced, plus provider behavior measurement before any optional metered dependency is treated as operationally important.

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

**Status: complete — final audit closed after PR #89**

Every currently executable network source is behind the governed runtime. The executable legacy-network allowance is empty. Brave remains optional/metered; without `BRAVE_SEARCH_API_KEY` it is not attempted and the zero-spend path remains usable.

The final audit did not pass on first inspection. It found that the repository-root `render.yaml` still prescribed paid Render `starter` services and persistent storage even though the roadmap required a zero-spend baseline. PR #89 moved that topology to `deploy/render-paid.yaml`, established `docs/ZERO_SPEND_RUNBOOK.md` as the default operating contract, and added CI coverage preventing a paid root Blueprint from silently becoming the baseline again.

PR #89 also closed an ownership-symmetry gap: every `ProviderStatus.DEVELOPMENT` provider must now correspond exactly to a current governed binding and process-wide runtime owner. ADR numbering is additionally checked for uniqueness and continuity. ADR 0050 records the deployment-authority correction; ADR 0051 records V2-D closure.

Source-run accounting is phase-proven. Policy/configuration/local-budget stops are non-attempts; completed zero-result calls are `not_found`; remote failures and malformed returned results count as attempts only when that phase is mechanically known. Generic phase-ambiguous validation remains unclassified rather than being guessed into failure metrics.

Retained-report ownership is canonicalized. Complete provider evidence and provenance have single retained owners; connected fields, M5 candidates and converged pivot/edge structures use validated references rather than duplicating values or locators. Historical self-contained retained formats remain readable through explicit read-only compatibility paths.

The reviewed-document chain is complete:

- deterministic candidate character spans and PDF page-span provenance;
- short-lived server-owned review state without raw-document retention;
- atomic confirm/reject/re-review/promotion with immutable candidate value/provenance;
- authenticated and CSRF-protected HTTP review actions;
- separate explicit retained-case execution from a currently confirmed, research-authorized server-owned candidate;
- private operator controls for review, promotion preview and separate case execution;
- retained seed provenance plus typed source execution/evaluation visibility in private case views.

Cross-layer closure guards keep catalog, binding, provider registry and process runtime ownership aligned. Required active recursive sources remain zero-spend eligible, and optional metered sources cannot silently become required baseline dependencies.

V2-D closure does **not** authorize another provider, larger recursion, paid baseline dependencies, wider retention or identity-probability claims. New source activation begins only after a fresh review of current official documentation, terms, quotas, cost, authentication, returned fields, contact risk and retention implications.

## M10 — evaluation and calibration laboratory

**Status: labelled cohort comparison established; broader representative evaluation remains**

Established:

- complete deterministic source-state/failure fixture coverage;
- provider attempt/failure/no-match/yield counters with explicit denominators;
- graph growth, depth, duplicate and budget-stop counters;
- label-gated wrong-pivot measurement;
- controlled graph-limit comparison through the production frontier policy;
- count-only cohort aggregation across independent labelled graph fixtures, without reliability/probability claims.

The initial M10 cohort deliberately mixes depth-limited, duplicate-heavy and provider-failure graph shapes. It is enough to stop one fixture from being mistaken for representative evidence, but it is not broad enough to authorize a production-policy change.

Still required before increasing recursion or changing correlation thresholds:

- broaden labelled synthetic/consented cohorts across additional lead kinds and source-yield/cost conditions;
- deterministic replay/factor ablations;
- labelled false-positive/false-negative and threshold analysis where defensible labels exist;
- provider cost/yield implications for larger frontier policies;
- no probability claim unless calibration evidence supports it.

Observation count is evidence yield, not evidence quality. Reliability percentages should not be published without controlled sample size and denominator semantics.

## Immediate next gate

V2-D is closed. Do not reopen its architecture casually when adding sources.

The next product phase is **reviewed source expansion**, one provider at a time. For each candidate source:

1. re-check current official API/standard documentation, terms, quota and cost;
2. prove the source can remain optional if it is metered or credentialed;
3. declare catalog capability, accepted/emitted lead kinds and source-policy state before execution;
4. add deterministic success/not-found/malformed/rate-limit/unavailable fixtures;
5. execute only through the existing governed runtime and typed source-run contract;
6. preserve canonical evidence/provenance ownership and the existing privacy boundary;
7. keep the product functional at zero spend when the new source is absent.

Bluesky admission and the bounded public-profile adapter now exist. PR #96 also adds an explicit attempted-but-neutral `withheld` source state so public-web opt-out and suspended/deactivated account responses do not pollute not-found or provider-failure metrics. Bluesky still remains `PLANNED`, unbound and absent from the process-wide runtime and quick-research path.

The next Bluesky block is atomic activation: recheck current official policy/cost, then move catalog review/status, source binding, provider status, shared `ProviderRuntime` ownership and quick-research/source-run integration together. Activation must keep generic username spraying impossible, preserve the minimal field allowlist, and retain deterministic success/not-found/opt-out/account-unavailable/malformed/rate-limit/transient fixtures.

Potential source candidates remain those already recorded in `docs/V2_SOURCE_EXPANSION_PLAN.md`; their presence there is not activation permission.

Production recursion remains depth 2 / 12 nodes. M10 evidence, not feature pressure, decides whether those limits change.

Success means the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
