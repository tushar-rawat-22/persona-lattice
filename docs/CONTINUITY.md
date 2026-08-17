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
- Verified main after PR #42: `e4cfcd1576d13112f944d8095ece99cd38742a48`
- PR #42 exact tested head: `9ab0289b2968ee9828fcb87d1da4f3013b9c0b71`
- PR #42 CI run: `32050781713`, success across API 3.11/3.13, dependency audits, Ruff, web and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

## Permanent evidence semantics

- Observations, factual Claims and correlation results remain separate.
- Every factual conclusion keeps provenance.
- A discovered clue is a research lead, not proof of identity.
- Same-handle reuse alone is weak evidence.
- M5 is deterministic evidence-strength triage, not identity probability.
- `calibration_status=uncalibrated` and `is_identity_claim=false` remain fixed.
- Contradictions/vetoes and stale evidence remain visible.
- Unknown, not-found, unavailable and budget-stopped are distinct outcomes.
- No AI/ML/embedding/biometric identity decision is in the correlation path.

## Permanent security, privacy and cost boundary

PersonaLattice may expand attributable public information and explicitly authorized data. It does not add private-account bypass, login/account-recovery enumeration, credentials/passwords/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact, or regulated eligibility decisioning.

The default product must remain usable with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations may exist only as optional extensions. Missing optional credentials must degrade explicitly rather than breaking baseline research.

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

PR #22. Capability, cost/credential/review state and zero-spend planning are separated from execution authority.

### V2-D — runtime consistency and architecture closure — active

Provider/runtime sequence completed so far:

- PR #24: source binding admission;
- PR #25: reusable `ProviderRuntime`;
- PR #26: Sherlock governed quick research;
- PR #27: GitHub governed runtime;
- PR #28: GitHub rate/regression repair;
- PR #29: process-wide shared runtime;
- PR #30: GitLab governed runtime;
- PR #31: Codeforces governed runtime;
- PR #32: public DNS governed runtime.

Source-state/report/evaluation sequence completed:

- PR #34: typed source-run state contract; ADR 0021;
- PR #35: deterministic privacy-bounded source-run projection; ADR 0022;
- PR #36: explicit execution outcome mapping; ADR 0023;
- PR #37: converged node `source_runs` projection; ADR 0024;
- PR #38: factual quick-research source-run population; ADR 0025;
- PR #40: deterministic aggregate/per-source evaluation counters; ADR 0026;
- PR #42: complete deterministic source state/reason fixture matrix; ADR 0027.

Current governed production sources: Sherlock, GitHub, GitLab, Codeforces and public DNS. The only remaining legacy network binding is optional metered Brave exact-match search. No new third-party source is authorized during architecture closure.

## Source-run and evaluation semantics

The retained source-run projection is intentionally privacy-minimal. It carries logical source name, lead kind, state/reason, observation count and execution/terminal flags only. Identifier values, source locators, provider payloads, credentials and exception text remain in their existing canonical owners.

Current typed distinctions:

- `executed / results_returned`: source execution completed with observations;
- `not_found / no_match`: source execution completed with zero observations;
- `unavailable / optional_not_configured`: optional source was not attempted;
- `budget_stopped / local_budget`: local policy stopped the source before provider contact;
- `unavailable / remote_rate_limit`: provider was attempted and rate-limited remotely;
- `unavailable / execution_failure`: execution was entered and failed;
- queued/review/display/blocked states remain available for scheduler/report integration.

PR #40 adds descriptive evaluation counters over those records. Counts are available globally and per logical source for attempts, completed attempts, attempted failures, result-bearing records, no-match results, admitted observation count, rate limits, execution failures, local budget stops, optional-unconfigured states and scheduler/review/display/blocked states.

PR #42 adds a deterministic synthetic matrix that covers every current `SourceRunState` and `SourceRunReason`. Vocabulary expansion now fails the matrix until its attempt/completion/failure semantics are reviewed explicitly. The matrix also proves aggregate/per-source evaluation is order-invariant and keeps local policy/configuration outcomes separate from remote provider failures.

Important interpretation rules:

- `not_found` is a completed lookup, not a provider failure;
- local budget stops and optional-unconfigured sources are not provider attempts;
- remote rate limits and proven execution failures are attempted failures;
- `unclassified_attempt_count` exists so future state drift cannot be silently forced into success/failure buckets;
- no reliability percentage, confidence score or identity-quality score is authorized from these counters yet.

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

1. Add deterministic graph-growth, duplicate and wrong-pivot measurements before changing recursion limits.
2. Add explicit typed outcomes for pre-execution policy/configuration and malformed-result cases only where the runtime can prove the state; do not guess from warning text.
3. Migrate the existing optional Brave path behind `ProviderRuntime` only if no-key zero-spend operation remains intact and no new source coverage is activated.
4. Remove the final legacy network allowance after that migration.
5. Finish document-candidate-to-reviewed-lead plumbing and operator source-state exposure.
6. Run final architecture consistency evaluation before activating new third-party sources.

Do not raise recursion limits or activate new third-party sources until the graph-growth/wrong-pivot/duplicate measurements exist and their denominators are understood.

## Update discipline

For each meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Public/operator prose and assistant-handover prose must remain separate.
