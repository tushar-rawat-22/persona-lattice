# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing
anything; commit, CI and provider-policy claims here are checkpoints, not a
substitute for inspection.

Never put API keys, real research identifiers, retained-case data, password
hashes, session material or unredacted investigation screenshots in this file.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only
- Verified pre-block `main`: `8191a049d334b4a77b48e23d6d00a4830d7473ba`
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

## Permanent evidence semantics

- Observations, factual Claims and correlation results remain separate.
- Every factual conclusion keeps provenance.
- A discovered clue is a research lead, not proof of identity.
- Same-handle reuse alone is weak evidence.
- M5 is deterministic evidence-strength triage, not identity probability.
- `calibration_status=uncalibrated` and `is_identity_claim=false` remain fixed.
- Contradictions/vetoes and stale evidence remain visible.
- Unknown, not-found and unavailable are distinct outcomes; do not infer a
  positive match from any of them.
- No AI/ML/embedding/biometric identity decision is in the correlation path.

## Permanent security/privacy/cost boundary

PersonaLattice may expand attributable public information and explicitly
authorized data. It does not add private-account bypass, login/account-recovery
enumeration, credentials/passwords/OTP/session/token collection, CAPTCHA/WAF/
proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device
IP discovery, live tracking, covert subject contact, or regulated eligibility
decisioning.

The V2 lead extractor blocks government-ID, credential/token and personal/device-
IP fields from recursive state and retains only blocked field names.

The default product must remain usable with zero paid APIs, zero paid database,
zero paid hosting requirement, zero paid proxy network and zero paid enrichment.
Metered integrations may exist only as optional extensions. Missing optional
credentials must degrade explicitly rather than breaking baseline research.

## Stable architecture

- Next.js UI: `apps/web`
- FastAPI API: `services/api`
- M1 evidence/persistence/normalization: `services/api/app/evidence`
- M2 bounded file intake: `services/api/app/uploads`
- M3 governed execution: `services/api/app/providers`
- M5 deterministic correlation: `services/api/app/correlation`
- convergence: `services/api/app/convergence.py`
- typed leads/frontier/source catalog/bindings/planning: `services/api/app/intelligence`
- retained cases: `services/api/app/cases.py`
- source expansion design: `docs/V2_SOURCE_EXPANSION_PLAN.md`

M0-M6 are complete. Private V1 one-admin research, retention/deletion, audit,
local HTTPS-tunnel acceptance and the ephemeral canonical evidence graph are
implemented. M5 remains uncalibrated and non-identity-claiming.

## V2 checkpoints

### V2-A — typed lead graph — complete

PR #20, merge `e66944259c545cdfe8e4020312357b92a42911ba`.
Exact-field lead extraction, M1-consistent normalization, dispositions, blocked
sensitive field classes and ADR 0010.

### V2-B — deterministic frontier — complete

PR #21, merge `2a69224e53ea1912879032548a38f017bfcafb6a`.
Post-merge CI `31974590505`: success. Reservation-safe frontier, duplicate/cycle
suppression, reason-coded outcomes and bounded additive lead-graph report state.
Depth/node ceilings remain 2/12.

### V2-C — capability registry/planner — complete

PR #22, merge `b1192fd15d73c144faba6279559db3e2b6ae2980`.
Post-merge CI `31974993479`: API 3.11/3.13, web and deployment image PASS. Source
capability, cost/credential/review state and zero-spend planning are separated
from execution authority.

### V2-D — runtime consistency — active

Completed migration sequence:

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

Current governed production sources: Sherlock, GitHub, GitLab, Codeforces and
public DNS. The only remaining legacy network binding is optional metered Brave
exact-match search.

This block adds `app.intelligence.source_states`: a typed report vocabulary for
`executed`, `not_found`, `queued`, `review_required`, `display_only`, `blocked`,
`unavailable` and `budget_stopped`, plus constrained reasons and invariants.
Important distinction: `not_found` proves execution completed; optional-not-
configured and local-budget outcomes prove that execution did not start. The
contract reports `execution_attempted`, not network transport, because local
deterministic sources can execute without network I/O. Only `executed` may retain
positive observation counts/source locators. ADR 0021 records the decision.

The contract is intentionally additive in this block. Existing retained report
payloads are not rewritten yet.

## Current deliberate limits

- convergence max depth: 2;
- convergence max nodes: 12;
- no new third-party adapter activation during V2-D closure;
- planned sources remain non-executable;
- newly discovered phone leads require review;
- contextual name/organization/location remain non-autonomous;
- public-search snippets do not become automatic identifier leads;
- no identity probability;
- no universal-account or hidden-identifier claims.

## Immediate next gate

1. Run CI for the source-state contract block and merge only if all required jobs
   pass.
2. Wire `SourceRunRecord` into convergence/retained report output and deterministic
   synthetic source fixtures without changing source coverage.
3. Migrate optional Brave behind `ProviderRuntime`, preserving actual caller
   purpose/consent and keeping no-key operation as the normal zero-spend path.
4. Remove the final legacy network allowlist after Brave migration.
5. Finish document-candidate-to-reviewed-lead plumbing and source-state UI/report
   exposure.
6. Start M10-style failure/growth evaluation before raising recursion limits or
   activating new network providers.

Brave policy note as of 2026-08-17: official Brave material describes Search as
metered with recurring credits and requires a subscription token. Treat that as
optional/metered, not as a guaranteed free dependency; re-check official terms
again before any later product activation change.

## Update discipline

For each meaningful block record verified main/branch/PR state, CI evidence,
behavior changes, explicit non-changes, corrected assumptions, unresolved risks
and the exact next gate. Keep public/operator prose separate from assistant
handover language.
