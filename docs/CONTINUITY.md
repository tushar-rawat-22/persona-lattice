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
- Verified implementation main after PR #56: `1b1d2066cc1c980578685b5ea4374468f61da819`
- PR #56 exact tested head: `915ccbf5286a7c5afdf4e6ab3ea961fde416552f`
- PR #56 CI run: `32088736604`, success across API 3.11/3.13, dependency audits, Ruff, web and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #56 adds the first fail-closed bridge from inert uploaded-document candidates into the typed lead path. Rule-extracted username/email/phone/URL candidates now retain character offsets into extracted text. `promote_confirmed_identifier_candidate()` accepts only candidates already confirmed and externally research-authorized by the human-review contract, reuses typed/M1 canonicalization and emits `REVIEWED_DOCUMENT_IDENTIFIER` provenance. It performs no provider call and does not itself enqueue work. ADR 0034 records the decision.

Two design flaws were corrected during the block rather than hidden:

1. PDF extraction currently flattens pages into one text string, so page provenance cannot be proved. PR #56 deliberately does not invent page numbers; `source_page` stays unset until the extractor emits structured page spans.
2. An early branch revision made rejection effectively irreversible. That was unnecessary state-machine policy. Final behavior is narrower: a rejected candidate is non-authorized and cannot promote, while a later explicit human review may change the decision.

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

Uploaded content is untrusted data. Extraction is never execution authority. A candidate enters the executable lead path only after an explicit human review/authorization action, and only for supported identifier kinds.

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

Document-intake checkpoint: PR #56. Character-span provenance and reviewed identifier promotion contract are implemented; PDF page-span provenance and operator/API wiring remain.

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

## Document candidate semantics

- file preview remains review-only and temp files are deleted after bounded extraction;
- candidate extraction may identify username, email, phone and URL values but does not authorize research;
- candidates carry artifact ID, candidate ID and deterministic extracted-text offsets where known;
- claims cannot become external-research leads;
- pending and rejected candidates cannot promote;
- a later explicit human review may reconfirm a previously rejected identifier;
- supported confirmed identifiers use the existing typed lead/M1 normalization path;
- names/organizations are not silently upgraded to executable research seeds;
- PDF page numbers are **not yet available** because the extractor flattens pages. Do not infer or fabricate them.

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

Add trustworthy PDF page-span provenance to bounded extraction before exposing the reviewed-document path as a complete operator workflow.

Requirements:

1. PDF extraction must return mechanically derived page boundaries/spans rather than inferred page numbers;
2. candidate character offsets and page attribution must remain consistent after page concatenation;
3. TXT and image metadata behavior must remain compatible;
4. page provenance must survive candidate review/promotion without copying raw document text into lead state;
5. uploaded text remains inert until explicit human review;
6. tests cover multi-page candidates, page boundaries, duplicate values across pages and malformed/empty-page behavior;
7. no new provider/API, credential, paid dependency, recursion expansion or identity-semantic change.

After page provenance, wire the explicit review/promotion action into the private operator/API flow, expose source-state/evaluation summaries cleanly, then run the final V2-D catalog/binding/runtime/report/privacy/zero-spend consistency review. Only after V2-D closure should new third-party providers be reviewed.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
