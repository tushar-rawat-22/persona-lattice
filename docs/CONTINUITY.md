# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Product: private evidence-first public/authorized research workbench
- Operating model: one authenticated operator; public route is demo/preview only
- Verified implementation main after PR #54: `2bb6cd052ac0ea64cf36ff57d1344dffaf6e9ac9`
- PR #54 exact tested head: `ae261e388835d904b0dcf6f05d07ffb7222a94ea`
- PR #54 CI run: `32085155838`, success across API 3.11/3.13, dependency audits, Ruff, web and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #54 moved the already-existing optional Brave exact-match search behind the shared `ProviderRuntime`, removed the final executable `legacy_research` network allowance and kept no-key operation as an explicit non-attempt. ADR 0033 records the decision.

A post-review flaw was fixed before merge: the first PR head converted an otherwise-unclassified provider validation error into `execution_failure`. The final head does not guess. Phase-ambiguous validation produces a warning and no source-run record, with a production-path regression test locking that rule. The one-argument Brave helper is explicitly documented as legacy compatibility, not typed production execution authority.

## Permanent evidence semantics

- Observations, factual Claims and correlation results remain separate.
- Every factual conclusion keeps provenance.
- A discovered clue is a research lead, not proof of identity.
- Same-handle reuse alone is weak evidence.
- M5 is deterministic evidence-strength triage, not identity probability.
- `calibration_status=uncalibrated` and `is_identity_claim=false` remain fixed.
- Contradictions/vetoes and stale evidence remain visible.
- Unknown, not-found, unavailable, blocked and budget-stopped remain distinct outcomes.
- No AI/ML/embedding/biometric identity decision is in the correlation path.

## Permanent security, privacy and cost boundary

Allowed scope is attributable public information and explicitly authorized data. PersonaLattice does not add private-account bypass, login/account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

The baseline must work with zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment. Metered integrations can exist only as optional extensions. Missing optional configuration must degrade explicitly rather than breaking baseline research.

Brave remains optional/metered. No `BRAVE_SEARCH_API_KEY` means no Brave attempt. Do not treat its existence in the runtime registry as permission to make it mandatory or to expand its query scope.

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

M0-M6 are complete. Private V1 one-admin research, retention/deletion, audit, local HTTPS-tunnel acceptance and the ephemeral canonical evidence graph are implemented.

## V2 checkpoint

### V2-A — typed lead graph — complete

PR #20. Exact-field lead extraction, M1-consistent normalization, typed dispositions and blocked sensitive field classes.

### V2-B — deterministic frontier — complete

PR #21. Reservation-safe frontier, duplicate/cycle suppression, reason-coded outcomes and bounded lead-graph report state. Production limits remain depth 2 / 12 nodes.

### V2-C — capability registry/planner — complete

PR #22. Capability, lifecycle/cost/configuration/review state and zero-spend planning are separated from execution authority.

### V2-D — runtime consistency and architecture closure — active

Current network execution ownership:

- Sherlock — governed runtime
- GitHub — governed runtime
- GitLab — governed runtime
- Codeforces — governed runtime
- public DNS — governed runtime
- optional Brave exact-match search — governed runtime
- executable legacy network allowance — **empty**

Key provider/runtime PRs: #24-#32, #50, #52, #54.

Key source-state/report/evaluation PRs: #34-#48. These establish typed source states/reasons, privacy-bounded projections, factual quick-research population, deterministic per-source counters, full-vocabulary fixture coverage, graph-growth/duplicate counters, label-gated wrong-pivot measurement and network-free graph-limit comparison through the real frontier scheduler.

## Source-run semantics

Retained source-run records carry logical source name, lead kind, state/reason, observation count and execution/terminal flags. They do not duplicate identifier values, source locators, provider payloads, secrets or exception text.

Critical distinctions:

- completed call with results → `executed / results_returned`;
- completed call with zero results → `not_found / no_match`;
- optional source absent → `unavailable / optional_not_configured`, no attempt;
- local budget stop → `budget_stopped / local_budget`, no provider contact;
- provider-policy rejection → blocked, no attempt;
- required server-side secret absent → unavailable, no attempt;
- remote rate limit / proven execution failure → unavailable, attempted;
- returned malformed result → unavailable, attempted only when post-attempt phase is mechanically proven;
- generic `ProviderValidationError` → no source-run record because its phase is ambiguous.

`source_provider_exception_record()` is the governed provider-exception mapping authority. Warnings are human context only and are never parsed into source state.

## Graph-evaluation semantics

Graph evaluation records growth, maximum depth, admitted pivots, duplicate suppression, provider failures and budget stops. Wrong-pivot truth requires explicit synthetic or consented relevance labels. Production pivots without labels remain unscored.

The graph-limit harness uses the real `LeadFrontier`. Its regression fixture shows that extra depth can admit both useful and wrong pivots; it is not authorization to raise production limits.

## Current deliberate limits

- convergence max depth: 2;
- convergence max nodes: 12;
- no new third-party provider activation during V2-D closure;
- planned sources remain non-executable;
- newly discovered phone leads require review;
- contextual name/organization/location remain non-autonomous;
- public-search snippets do not become automatic identifier leads;
- Brave remains optional and excluded from the zero-spend requirement;
- no identity probability or universal-account claims.

## Immediate next gate

Build the document-candidate-to-reviewed-lead boundary.

Requirements:

1. extracted document candidates remain inert by default;
2. only an explicit review/promotion action can create a research lead;
3. only supported lead kinds may be promoted;
4. file/page/offset or equivalent extraction provenance survives promotion;
5. uploaded text never becomes execution authority;
6. promotion must enter the existing typed lead/frontier policy rather than creating a parallel research path;
7. tests must cover duplicate promotion, rejected/unsupported candidates, provenance preservation and sensitive-field fail-closed behavior.

After that, expose source-state/evaluation summaries cleanly to the operator and run the final V2-D catalog/binding/runtime/report/privacy/zero-spend consistency review. Only then review new third-party providers.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
