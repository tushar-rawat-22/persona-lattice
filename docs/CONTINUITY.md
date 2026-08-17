# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Do not put API keys, real research identifiers, retained-case data, password hashes, session material or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only
- Verified implementation main after PR #52: `9b4fab9f86b4e9bf5e12689cb91fbcde09a3a269`
- PR #52 exact tested head: `ef1ee81b47234e887fcc26a2c3057649c03d906b`
- PR #52 CI run: `32076607311`, success across API 3.11/3.13, dependency audits, Ruff, web and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #52 removes quick research's competing governed-provider exception classifier. Governed provider failures now use `source_provider_exception_record()` for phase-proven source-run semantics. Injected compatibility callables remain an explicit exception because their invocation is itself a known attempt boundary.

ADR 0032 records this decision. The next architecture gate is the already-existing optional Brave exact-match migration; no new provider is authorized yet.

## Permanent evidence semantics

- Observations, factual Claims and correlation results remain separate.
- Every factual conclusion keeps provenance.
- A discovered clue is a research lead, not proof of identity.
- Same-handle reuse alone is weak evidence.
- M5 is deterministic evidence-strength triage, not identity probability.
- `calibration_status=uncalibrated` and `is_identity_claim=false` remain fixed.
- Contradictions/vetoes and stale evidence remain visible.
- Unknown, not-found, unavailable, blocked and budget-stopped are distinct outcomes.
- No AI/ML/embedding/biometric identity decision is in the correlation path.

## Permanent security, privacy and cost boundary

PersonaLattice may expand attributable public information and explicitly authorized data. It does not add private-account bypass, login/account-recovery enumeration, credentials/passwords/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact, or regulated eligibility decisioning.

The default product must remain usable with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations may exist only as optional extensions. Missing optional configuration must degrade explicitly rather than breaking baseline research.

## Stable architecture

- Next.js UI: `apps/web`
- FastAPI API: `services/api`
- M1 evidence/persistence/normalization: `services/api/app/evidence`
- M2 bounded file intake: `services/api/app/uploads`
- M3 governed execution: `services/api/app/providers`
- M5 deterministic correlation: `services/api/app/correlation`
- convergence: `services/api/app/convergence.py`
- typed leads/frontier/source catalog/bindings/planning/reporting/evaluation: `services/api/app/intelligence`
- quick research: `services/api/app/research.py`
- retained cases: `services/api/app/cases.py`
- source expansion design: `docs/V2_SOURCE_EXPANSION_PLAN.md`

M0-M6 are complete. Private V1 one-admin research, retention/deletion, audit, local HTTPS-tunnel acceptance and the ephemeral canonical evidence graph are implemented. M5 remains uncalibrated and non-identity-claiming.

## V2 checkpoints

### V2-A — typed lead graph — complete

PR #20. Exact-field lead extraction, M1-consistent normalization, dispositions, blocked sensitive field classes and ADR 0010.

### V2-B — deterministic frontier — complete

PR #21. Reservation-safe frontier, duplicate/cycle suppression, reason-coded outcomes and bounded additive lead-graph report state. Depth/node ceilings remain 2/12.

### V2-C — capability registry/planner — complete

PR #22. Capability, cost/configuration/review state and zero-spend planning are separated from execution authority.

### V2-D — runtime consistency and architecture closure — active

Provider/runtime sequence completed:

- PR #24: source binding admission;
- PR #25: reusable `ProviderRuntime`;
- PR #26: Sherlock governed quick research;
- PR #27: GitHub governed runtime;
- PR #28: GitHub rate/regression repair;
- PR #29: process-wide shared runtime;
- PR #30: GitLab governed runtime;
- PR #31: Codeforces governed runtime;
- PR #32: public DNS governed runtime;
- PR #50: phase-proven runtime validation boundary plus shared provider-exception mapper; ADR 0031;
- PR #52: quick research adopts the shared mapper; ADR 0032.

Source-state/report/evaluation sequence completed:

- PR #34: typed source-run state contract; ADR 0021;
- PR #35: deterministic privacy-bounded source-run projection; ADR 0022;
- PR #36: explicit execution outcome mapping; ADR 0023;
- PR #37: converged node `source_runs` projection; ADR 0024;
- PR #38: factual quick-research source-run population; ADR 0025;
- PR #40: deterministic aggregate/per-source evaluation counters; ADR 0026;
- PR #42: complete deterministic source state/reason fixture matrix; ADR 0027;
- PR #44: deterministic graph-growth/duplicate counters plus label-gated wrong-pivot measurement; ADR 0028;
- PR #46: deterministic labelled graph-limit comparison through the real `LeadFrontier`; ADR 0029;
- PR #48: provider-policy/missing-secret/malformed-result source outcome vocabulary and privacy-safe evaluation counters; ADR 0030.

Current governed production sources: Sherlock, GitHub, GitLab, Codeforces and public DNS. The only remaining legacy network binding is optional metered Brave exact-match search. No new third-party source is authorized during architecture closure.

## Source-run semantics after PR #52

The retained source-run projection is intentionally privacy-minimal. It carries logical source name, lead kind, state/reason, observation count and execution/terminal flags only. Identifier values, source locators, provider payloads, secrets and exception text remain in their existing canonical owners.

Typed distinctions include:

- `executed / results_returned`: completed execution with observations;
- `not_found / no_match`: completed execution with zero observations;
- `unavailable / optional_not_configured`: optional source was not attempted;
- `budget_stopped / local_budget`: local policy stopped execution before provider contact;
- `blocked / provider_policy`: provider policy rejected execution before an attempt;
- `unavailable / credential_not_configured`: required server-side secret was absent before an attempt;
- `unavailable / remote_rate_limit`: provider was attempted and rate-limited remotely;
- `unavailable / execution_failure`: execution was entered and failed;
- `unavailable / malformed_result`: provider output was returned but failed a proven post-attempt result check;
- queued/review/display/blocked policy states remain available for scheduler/report integration.

`ProviderResultValidationError` proves the post-attempt malformed-result phase for invalid returned result contracts, non-serializable returned payloads and blank returned source locators. `ProviderResponseTooLarge` is also post-attempt and remains its existing type.

Critical rule: generic `ProviderValidationError` maps to no source-run record. It can be raised before provider contact for request/provider mismatches and must not be guessed into `malformed_result`. `ProviderPolicyError`, missing-server-secret `ProviderAuthError`, and local rate-budget rejection are pre-attempt.

`source_provider_exception_record()` is the single governed provider-exception mapper. Quick research now delegates to it. Injected compatibility lookups still run outside `ProviderRuntime`; an otherwise-unclassified exception from an invoked injected callable may be recorded as generic `execution_failure` because invocation proves the attempt. Typed policy/configuration/local-budget outcomes keep their normal shared semantics.

Warnings are operator-facing context only. They are not parsed to derive source state. Exception text is not copied into retained source-run records.

Evaluation counters separate malformed attempted failures, local/policy/configuration non-attempts and remote attempted failures. The public evaluation projection deliberately uses `missing_secret_config_count` rather than a key containing the forbidden privacy token `credential`.

## Graph-evaluation semantics

PR #44 adds structural graph counters for node/edge growth, maximum depth, admitted pivots, duplicate suppression, provider failures, budget stops and review/display/blocked decisions. Evaluation fails closed if edge count, admitted pivots and non-seed node count drift or node depth is invalid.

Wrong-pivot truth is never inferred from usernames, provider agreement, graph shape or M5. It requires explicit `PivotRelevance` labels from deterministic synthetic fixtures or explicitly consented evaluation sets. Labels for non-admitted keys fail closed. Unlabelled admitted pivots remain visible and unscored.

PR #46 adds a network-free limit-comparison harness through the real `LeadFrontier`. Production convergence and evaluation share `compatibility_frontier_limits()`. The regression fixture shows that depth 3 can both admit more relevant evidence and admit more wrong pivots; it is not authorization to change production limits.

## Current deliberate limits

- convergence max depth: 2;
- convergence max nodes: 12;
- no new third-party adapter activation during V2-D closure;
- planned sources remain non-executable;
- newly discovered phone leads require review;
- contextual name/organization/location remain non-autonomous;
- public-search snippets do not become automatic identifier leads;
- Brave remains optional and must not be required for zero-spend operation;
- no identity probability;
- no universal-account or hidden-identifier claims.

## Immediate next gate

1. Migrate the existing optional Brave exact-match path behind `ProviderRuntime` without changing query scope or source coverage. No-key operation must remain an explicit non-attempt and the baseline must remain zero-spend.
2. Remove the final `legacy_research` network allowance after Brave is governed.
3. Finish document-candidate-to-reviewed-lead plumbing and operator source-state/evaluation exposure.
4. Run final architecture consistency evaluation before activating new third-party sources.

Production recursion remains depth 2 / 12 nodes. Do not raise it from the single regression fixture; representative synthetic/consented labelled evaluation and provider cost/yield implications are still required.

## Update discipline

For each meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Public/operator prose and assistant-handover prose must remain separate.
