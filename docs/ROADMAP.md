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

Repository and CI, evidence/provenance model, normalization, bounded file intake, governed provider framework, reviewed Sherlock discovery, deterministic M5 correlation and the local evidence dashboard are implemented.

M5 permanent outputs remain:

- `calibration_status=uncalibrated`
- `is_identity_claim=false`

## M7 — private one-admin research product

**Status: implemented and manually accepted locally**

The private product has one deployment-configured admin, Argon2 password verification, HttpOnly sessions, CSRF protection, a private `/admin` route, same-origin API proxying, retained cases, delete/expiry controls and live bounded research.

Current live research sources include reviewed Sherlock, GitHub, GitLab, Codeforces, phone numbering-plan metadata and public DNS infrastructure metadata. Brave exact public-web search is optional when configured.

Local HTTPS-tunnel acceptance proves the operator path. It is not a requirement to buy durable hosting; local/self-hosted operation remains the zero-spend baseline.

## M8 — privacy lifecycle and operations

**Status: substantially implemented**

Implemented:

- 30-day default retained-case lifecycle;
- automatic expiry purge and explicit deletion;
- privacy-safe audit events;
- secrets outside Git;
- bounded request, concurrency, timeout and response limits.

Remaining operational work is limited to backup/restore design if a persistent production store is introduced, plus provider behavior measurement before any optional metered dependency is treated as operationally important.

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

**Status: active; network migration, reviewed-document backend execution, cross-layer ownership/zero-spend guard, source-run contract closure and retained provider-provenance ownership are complete**

Every currently executable network source is behind the governed runtime. Key migration checkpoints are PRs #24-#32, #50, #52 and #54. The executable legacy network allowance is empty.

Brave remains an optional metered extension. Without `BRAVE_SEARCH_API_KEY`, it is not attempted and the zero-spend research path continues with the remaining sources.

Source-run accounting is phase-proven. Policy/configuration/local-budget stops are non-attempts; completed zero-result calls are `not_found`; remote failures and malformed returned results count as attempts only when that phase is mechanically known. Generic phase-ambiguous validation is left unclassified rather than guessed into a failure count.

Source-state/report/evaluation work in PRs #34-#48 establishes typed source states/reasons, privacy-bounded projections, factual quick-research population, deterministic aggregate/per-source counters, full-vocabulary fixture coverage, graph-growth/duplicate counters, label-gated wrong-pivot measurement and network-free graph-limit comparison through the real frontier scheduler.

PR #70 closes the stale convergence compatibility shim that treated a missing `source_runs` contract as an empty report. Converged reports now require the canonical `QuickResearchReport.source_runs` field directly; a valid zero-record tuple still yields the same privacy-bounded empty projection. ADR 0041 records the decision.

PR #72 closes retained quick-report full-evidence duplication. Complete provider evidence has one canonical retained owner in top-level quick observations. Account-candidate and contradiction classification refer back to observations by index. ADR 0042 records the decision.

PR #74 closes converged M5 candidate-provenance duplication. New evaluations retain `candidate_node` plus `candidate_observation_index`; the private UI resolves those references while retaining read-only compatibility for older retained cases. ADR 0043 records the decision.

PR #77 closes converged pivot-provenance duplication. Canonical node observations own provider source/locator; lead decisions use `source_observation_index`; admitted edges use `lead_decision_index`. New reference readers fail closed on missing, malformed, out-of-range or structurally inconsistent references. `CaseStore` temporarily hydrates legacy edge display fields for the current admin UI without writing those copies back to SQLite. ADR 0044 records the decision.

PR #79 closes the remaining quick structured-report value/provenance duplication. New `connected_identifiers` entries retain only connected-field kind, canonical observation index, reviewed detail-field name and status. The canonical quick observation is now the sole retained owner of the selected value, provider source and source locator. `CaseStore` hydrates the old display shape only in returned responses so the current UI and historical cases remain readable. Mixed, malformed or out-of-range references fail closed. ADR 0045 records the decision.

The document-review path has a complete server-owned backend chain:

- PR #56: deterministic candidate spans and fail-closed reviewed identifier promotion;
- PR #58: extraction-time PDF page spans and corrected flattened-text limits;
- PR #60: short-lived SQLite review state without raw-document retention;
- PR #62/#63: atomic confirm/reject/re-review/promotion with immutable candidate value/provenance;
- PR #64: authenticated, CSRF-protected HTTP review actions;
- PR #66: separate explicit retained-case execution from a currently confirmed, research-authorized server-owned candidate.

The PR #66 execution action accepts artifact/candidate IDs plus mode, purpose and consent acknowledgement. It reloads and revalidates current review state immediately before execution, never accepts a browser-supplied reviewed identifier, and preserves the existing `artifact://` page/character provenance in the retained case. Review confirmation and promotion remain non-executing state transitions.

PR #68 adds a cross-layer closure guard derived from live declarations. Governed executable bindings must exactly match process-wide runtime adapter ownership, runtime adapters must use the reviewed registry descriptors, and planned/unreviewed sources cannot silently enter production runtime ownership. The same guard requires every required `ACTIVE` recursive source to stay zero-spend eligible; any current recursive source that is not zero-spend eligible must remain `OPTIONAL`. ADR 0040 records the decision.

Remaining before V2-D closes:

1. expose document review/run controls and existing source-state/evaluation summaries cleanly in the private operator UI;
2. migrate the private quick connected-field UI to canonical observation references and remove the temporary connected-field response hydration for new reports;
3. migrate the private converged-edge UI to decision/observation references and remove the temporary edge response hydration for new reports;
4. close any remaining compatibility seam only where doing so does not break historical retained cases, operator behavior or evidence semantics.

No new third-party source should be activated during these closure blocks.

## M10 — evaluation and calibration laboratory

**Status: deterministic evaluation contracts established; representative labelled evaluation remains**

Established:

- complete deterministic source-state/failure fixture coverage;
- provider attempt/failure/no-match/yield counters with explicit denominators;
- graph growth, depth, duplicate and budget-stop counters;
- label-gated wrong-pivot measurement;
- controlled graph-limit comparison through the production frontier policy.

Still required before increasing recursion or changing correlation thresholds:

- multiple defensible synthetic/consented labelled fixture families;
- deterministic replay/factor ablations;
- labelled false-positive/false-negative and threshold analysis where defensible labels exist;
- provider cost/yield implications for larger frontier policies;
- no probability claim unless calibration evidence supports it.

Observation count is evidence yield, not evidence quality. Reliability percentages should not be published without controlled sample size and denominator semantics.

## Immediate next gate

The retained backend ownership audit is now closed for quick complete provider payloads, quick connected-field values/provenance, converged M5 candidates and converged pivot provenance. The next useful V2-D block is the private operator UI contract migration: resolve quick connected fields and converged edges from canonical references in the browser, then remove the corresponding temporary response-hydration paths for new reports while keeping historical retained cases readable.

The same operator block should begin exposing reviewed-document state, explicit case execution, source-state/evaluation summaries and retained seed provenance without re-deriving backend authorization or evidence semantics in the browser.

Only after V2-D closure should new public/API sources be reviewed one at a time, with current official terms, authentication, limits and cost rechecked before activation.

Production recursion remains depth 2 / 12 nodes.

Success means the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
