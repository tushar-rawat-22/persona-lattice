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
- Verified implementation main after PR #60: `0e0c1df75ffa9c7a3d254386116723563dfffe4b`
- PR #60 exact tested head: `afd9bf7a1728cba4e3b2c5a97c3fb1dc531b2a81`
- PR #60 CI run: `32096166715`, success across API 3.11/3.13, dependency audits, Ruff, web and deployment image
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`

PR #60 closes the server-owned-state prerequisite for document-candidate review. Successful bounded file preview now persists each extracted `ReviewCandidate` in a short-lived SQLite review table keyed by artifact ID and candidate ID. The store uses the existing `PERSONALATTICE_DB_PATH`, so it adds no service or paid dependency.

Review persistence is intentionally narrower than the preview response. It keeps the normalized candidate value, identifier kind, review state, artifact/candidate IDs and mechanically derived page/character provenance needed for later authorization. It does not copy uploaded file bytes, filenames, file hashes, surrounding extracted text or the complete extracted document into review state. Default review retention is 24 hours and can be configured only within 1–168 hours through `PERSONALATTICE_UPLOAD_REVIEW_RETENTION_HOURS`.

The stored payload is not trusted blindly: reads verify that candidate/artifact IDs inside the serialized candidate still match the row keys. Tests also prove that raw surrounding document prose and filenames are absent from the SQLite/WAL review persistence. Two weak test assumptions were corrected before CI: a username fixture's end offset was off by one, and the first tamper regression only changed a row key in a way that bypassed the decoder. The corrected tamper test changes serialized provenance so the fail-closed decoder is actually exercised.

ADR 0036 records the decision. `ArtifactPreview.storage_retained=false` still means uploaded artifact bytes are not retained; short-lived candidate review metadata is a separate authorization record.

PR #60 deliberately does not expose confirm/reject/promotion HTTP actions. That separation is intentional: adding endpoints before trusted server-owned candidate state existed would have forced the API to accept browser-supplied candidate values/provenance as authority.

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
- PR #58: extraction-time PDF page spans plus exact candidate page attribution and corrected flattened-text output bounds;
- PR #60: short-lived server-owned candidate review persistence, bounded retention and stored-provenance integrity checks without raw document retention.

Operator/API review mutation wiring remains incomplete. The server now owns the candidate record needed for authorization, but there is no authenticated endpoint yet for confirm, reject, re-review or promotion.

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
- successful preview persists only short-lived candidate review metadata, not uploaded file bytes or complete extracted text;
- candidate review state defaults to 24-hour retention and expires independently of retained research cases;
- server lookup requires both artifact ID and candidate ID and validates stored payload provenance against row keys;
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

Expose the server-owned reviewed-document decision path through the private operator/API boundary.

Requirements:

1. mutation requests carry artifact/candidate IDs and an explicit human decision, never a browser-supplied candidate value/provenance/authorization flag as authority;
2. endpoints require the existing authenticated write/CSRF boundary;
3. unknown or expired artifact/candidate IDs fail closed without echoing candidate values;
4. confirm/reject/re-review transitions reload and update the PR #60 server-owned record;
5. confirmed identifier promotion reuses `promote_confirmed_identifier_candidate()` rather than creating a second promotion path;
6. artifact ID, candidate ID, character offsets and PR #58 page provenance survive into the promoted lead without copying raw uploaded text;
7. claim candidates and unsupported identifier kinds remain non-executable;
8. promotion itself does not automatically call any provider;
9. tests cover authentication/CSRF, stale or unknown IDs, attempted browser tampering, confirm/reject/re-review and successful promotion;
10. no provider/API, credential, paid dependency, recursion expansion or identity-semantic change.

After operator/API review wiring, expose source-state/evaluation summaries cleanly, then run the final V2-D catalog/binding/runtime/report/privacy/zero-spend consistency review. Only after V2-D closure should new third-party providers be reviewed.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
