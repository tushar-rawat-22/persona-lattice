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
- Verified implementation main after PR #58: `1e8a8005bff307bd456542a656c81509a5bd1e7f`
- PR #58 exact tested head: `997544bd10e65ccb272b997093727d173873d585`
- PR #58 CI run: `32092648629`, success across API 3.11/3.13, dependency audits, Ruff, web and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #58 closes the PDF page-attribution gap left deliberately open by PR #56. The bounded PDF extractor now returns a `PageTextSpan` for every parsed page using one-based page numbers and half-open global character intervals over the exact flattened `extracted_text`. The page map crosses the process boundary with the extraction result and is returned in `ArtifactPreview`.

Candidate page attribution is fail-closed: `source_page` is set only when the candidate's full source interval is contained by exactly one extractor-proven page span. A span crossing a page separator has no page claim. Empty PDF pages remain zero-length spans so later offsets cannot drift. Normalized duplicate identifiers still collapse to one candidate under the existing contract; the first occurrence owns the retained provenance.

Two flaws were corrected during the block rather than preserved:

1. The previous PDF output limit counted page text but not the newline separators inserted into the returned flattened string. PR #58 makes the limit cover the actual returned text, separators included.
2. The first boundary regression fixture assumed the phone extractor could match across a newline, which its reviewed regex deliberately cannot. CI exposed that bad fixture. The corrected test exercises the page-span mapper directly instead of changing identifier extraction to satisfy an invalid test assumption.

`ArtifactPreview` now validates that page numbers are contiguous, page spans align with flattened character boundaries, every inter-page separator is actually a newline, and the last span ends at the extracted-text boundary. ADR 0035 records the decision.

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

Document-intake checkpoints:

- PR #56: deterministic candidate character spans plus fail-closed reviewed identifier promotion contract;
- PR #58: extraction-time PDF page spans plus exact candidate page attribution and corrected flattened-text output bounds.

Operator/API review wiring remains incomplete. The current contracts are backend primitives; they do not yet provide a durable private workflow for confirming/rejecting a preview candidate and promoting only server-owned confirmed state.

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
- PDF candidates may additionally carry a mechanically proven one-based `source_page`;
- PDF page spans are half-open intervals over the exact returned flattened text; separators belong to neither page;
- empty PDF pages are retained as zero-length spans in the page map;
- a candidate receives no page claim unless its full source interval belongs to exactly one page;
- claims cannot become external-research leads;
- pending and rejected candidates cannot promote;
- a later explicit human review may reconfirm a previously rejected identifier;
- supported confirmed identifiers use the existing typed lead/M1 normalization path;
- names/organizations are not silently upgraded to executable research seeds.

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

Wire the existing reviewed-document candidate contract into the private operator/API flow.

Requirements:

1. candidate state used for confirm/reject/promotion must be server-owned; do not accept browser-supplied authorization flags as authority;
2. previewed document text remains inert until an explicit authenticated human review action;
3. confirmed identifier promotion must reuse `promote_confirmed_identifier_candidate()` rather than creating a second promotion path;
4. artifact ID, candidate ID, character offsets and PR #58 page provenance must survive into the promoted lead without copying raw uploaded text;
5. claim candidates and unsupported identifier kinds remain non-executable;
6. rejection remains non-authorizing while later explicit re-review stays possible;
7. tests must cover authentication/CSRF, stale or unknown candidate IDs, tampered candidate values/provenance, confirm/reject/re-review and successful promotion;
8. no provider/API, credential, paid dependency, recursion expansion or identity-semantic change.

After operator/API review wiring, expose source-state/evaluation summaries cleanly, then run the final V2-D catalog/binding/runtime/report/privacy/zero-spend consistency review. Only after V2-D closure should new third-party providers be reviewed.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
