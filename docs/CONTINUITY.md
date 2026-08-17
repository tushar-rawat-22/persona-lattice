# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; commit, CI and provider-policy claims here are checkpoints, not a substitute for inspection.

Never put API keys, real research identifiers, retained-case data, password hashes, session material or unredacted investigation screenshots in this file.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only
- Verified `main` before PR #38: `35c4428916c9a5d5fe30ca21fbdc2b98fb4bc0a0`
- PR #38: `v2-quick-source-run-facts`; implementation/docs head before this continuity refresh: `17286fa787e30b98790e3af7a8f5a34399c6cdda`
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

## Permanent security/privacy/cost boundary

PersonaLattice may expand attributable public information and explicitly authorized data. It does not add private-account bypass, login/account-recovery enumeration, credentials/passwords/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact, or regulated eligibility decisioning.

The V2 lead extractor blocks government-ID, credential/token and personal/device-IP fields from recursive state and retains only blocked field names.

The default product must remain usable with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations may exist only as optional extensions. Missing optional credentials must degrade explicitly rather than breaking baseline research.

## Stable architecture

- Next.js UI: `apps/web`
- FastAPI API: `services/api`
- M1 evidence/persistence/normalization: `services/api/app/evidence`
- M2 bounded file intake: `services/api/app/uploads`
- M3 governed execution: `services/api/app/providers`
- M5 deterministic correlation: `services/api/app/correlation`
- convergence: `services/api/app/convergence.py`
- typed leads/frontier/source catalog/bindings/planning/reporting: `services/api/app/intelligence`
- quick research: `services/api/app/research.py`
- retained cases: `services/api/app/cases.py`
- source expansion design: `docs/V2_SOURCE_EXPANSION_PLAN.md`

M0-M6 are complete. Private V1 one-admin research, retention/deletion, audit, local HTTPS-tunnel acceptance and the ephemeral canonical evidence graph are implemented. M5 remains uncalibrated and non-identity-claiming.

## V2 checkpoints

### V2-A — typed lead graph — complete

PR #20, merge `e66944259c545cdfe8e4020312357b92a42911ba`. Exact-field lead extraction, M1-consistent normalization, dispositions, blocked sensitive field classes and ADR 0010.

### V2-B — deterministic frontier — complete

PR #21, merge `2a69224e53ea1912879032548a38f017bfcafb6a`. Post-merge CI `31974590505`: success. Reservation-safe frontier, duplicate/cycle suppression, reason-coded outcomes and bounded additive lead-graph report state. Depth/node ceilings remain 2/12.

### V2-C — capability registry/planner — complete

PR #22, merge `b1192fd15d73c144faba6279559db3e2b6ae2980`. Post-merge CI `31974993479`: API 3.11/3.13, web and deployment image PASS. Capability, cost/credential/review state and zero-spend planning are separated from execution authority.

### V2-D — runtime consistency and source-state closure — active

Runtime migration sequence:

- PR #24: source binding admission; merge `a92afe8ddc12a16d837e95f575660f838d39af28`;
- PR #25: reusable `ProviderRuntime`; merge `0759ea2d514b9606e8ac31bf700d8e75afa6dc1c`;
- PR #26: Sherlock governed quick research; next main checkpoint `2d0a3dc54b00b81047a69274ca2ec1da3148f7cd`;
- PR #27: GitHub governed runtime; merge `fb4e672c438103588bacc0f7190ef116796dd0ac`;
- PR #28: GitHub rate/regression repair; merge `69b0d462f9a45f0440dd867bdd96a674e0b7ebb0`;
- PR #29: process-wide shared runtime; merge `a12174b05caabd880e947603845420f63ffa8c67`;
- PR #30: GitLab governed runtime; merge `a001d902ed807f6e7c7e61d94d8aeae40e8239dc`;
- PR #31: Codeforces governed runtime; merge `111788f8daf96805a6456202d5b2a702d554f534`;
- PR #32: public DNS governed runtime; merge `66410eff175bc4cee09460cac0c33584f937f628`;
- PR #33: documentation standard; merge `8191a049d334b4a77b48e23d6d00a4830d7473ba`.

Source-state/report sequence:

- PR #34: typed source-run state contract; merge `1a8d875396b8ad6730416d3373ad5b4f8bd09650`; ADR 0021;
- PR #35: deterministic privacy-bounded source-run report projection; merge `ff876d92b969aa6657ce23f0329d61104d4141eb`; ADR 0022;
- PR #36: explicit execution outcome mapping; merge `e26158720f78a9db8972235142a900394c8a4b9e`; ADR 0023;
- PR #37: converged node `source_runs` projection; merge `35c4428916c9a5d5fe30ca21fbdc2b98fb4bc0a0`; ADR 0024; exact PR head CI run `32039578511` succeeded;
- PR #38: quick-research factual source-run population; ADR 0025; under review at this checkpoint.

Current governed production sources: Sherlock, GitHub, GitLab, Codeforces and public DNS. The only remaining legacy network binding is optional metered Brave exact-match search. No new third-party source is authorized during architecture closure.

## Source-run semantics

The retained source-run projection is intentionally privacy-minimal. It carries logical source name, lead kind, state/reason, observation count and execution/terminal flags only. Identifier values, source locators, provider payloads, credentials and exception text remain in their existing canonical owners and are not copied into this projection.

Current typed distinctions:

- `executed / results_returned`: source execution completed with observations;
- `not_found / no_match`: source execution completed with zero observations;
- `unavailable / optional_not_configured`: optional source was not attempted;
- `budget_stopped / local_budget`: local policy stopped the source before provider contact;
- `unavailable / remote_rate_limit`: provider was attempted and rate-limited remotely;
- `unavailable / execution_failure`: execution was entered and failed;
- queued/review/display/blocked states remain available for scheduler/report integration.

PR #38 makes normal quick research populate these facts instead of leaving the converged projection empty. It deliberately refuses to call ambiguous policy/auth/preflight exceptions an attempted provider failure when the execution boundary cannot prove provider contact.

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

1. Merge PR #38 only after the exact latest head passes API 3.11/3.13, Ruff/audits, web and deployment-image CI.
2. Add explicit typed outcomes for pre-execution policy/configuration failures and malformed-result cases where the current boundary can prove them; do not guess from warning text.
3. Add source reliability/budget evaluation counters over the retained source-run projection before changing recursion limits.
4. Migrate the existing optional Brave path behind `ProviderRuntime` only if the migration preserves no-key zero-spend operation and does not activate any new source coverage.
5. Remove the final legacy network allowlist after that migration.
6. Finish document-candidate-to-reviewed-lead plumbing and source-state operator exposure.
7. Start M10-style failure/growth evaluation before raising recursion limits or activating new network providers.

Brave policy note as of 2026-08-17: existing project review classifies Search as metered/credentialed and therefore optional. Re-check official terms and quotas from primary sources before any later activation or cost-policy change.

## Update discipline

For each meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Public/operator prose and assistant-handover prose must remain separate.
