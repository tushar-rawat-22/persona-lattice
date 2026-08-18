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

**Status: active; network runtime migration and document-review HTTP boundary complete**

Provider/runtime migration is complete for every currently executable network source:

- PR #24: source binding admission;
- PR #25: storage-independent `ProviderRuntime`;
- PR #26: Sherlock governed quick research;
- PR #27/#28: GitHub migration and rate-policy repair;
- PR #29: one process-wide production runtime;
- PR #30: GitLab migration;
- PR #31: Codeforces migration;
- PR #32: public DNS migration;
- PR #50: phase-proven provider result validation and shared exception mapping;
- PR #52: quick research adopts the shared phase-proven mapper;
- PR #54: optional Brave exact-match search migrates to the shared runtime and the legacy network execution allowance becomes empty.

PR #54 does not make Brave part of the zero-spend baseline. With no `BRAVE_SEARCH_API_KEY`, Brave is not attempted and research continues with the remaining sources. The compatibility one-argument Brave helper is not typed production authority; production quick research sends the real lead kind, purpose and consent context directly through `ProviderRuntime`.

Source-run accounting remains phase-proven. Policy/configuration/local-budget stops are non-attempts; completed zero-result calls are `not_found`; remote failures and malformed returned results count as attempts only when that phase is mechanically known. Generic phase-ambiguous provider validation remains unclassified rather than being guessed into a failure count.

Completed source-state/report/evaluation work includes PRs #34-#48: typed source states and reasons, privacy-bounded projections, factual quick-research population, deterministic aggregate/per-source counters, a complete source-state fixture matrix, graph-growth/duplicate counters, label-gated wrong-pivot measurement and network-free graph-limit comparison through the real frontier scheduler.

PR #56 adds the first document-candidate promotion contract. Rule-extracted username/email/phone/URL candidates retain deterministic extracted-text character spans and can enter the typed lead path only after explicit human review authorization. Claims, pending/rejected candidates and non-executable identifier kinds remain non-executable. Promoted leads carry artifact/candidate/span provenance without copying uploaded text.

PR #58 closes the PDF page-attribution gap. The bounded extractor now returns one-based half-open page spans over the exact flattened text, including zero-length spans for empty pages. Candidates receive `source_page` only from exact span containment; page numbers are never inferred after flattening. The PDF output-size limit now also counts the newline separators inserted between pages, so the configured character ceiling bounds the actual returned text.

PR #60 adds the server-owned review-state prerequisite for operator actions. Successful file preview writes each extracted `ReviewCandidate` to the existing local SQLite database under artifact ID + candidate ID, with a 24-hour default retention window. The review store keeps only the normalized candidate value, kind, review state and page/character provenance needed for later authorization; it does not retain uploaded file bytes, filenames, hashes, surrounding extracted text or the complete extracted document. Stored candidate/artifact IDs are revalidated on read so later review actions do not need to trust browser-supplied candidate objects.

PR #62/#63 add and harden the server-owned review mutation authority. Confirm, reject and re-review mutate only the current SQLite record identified by artifact ID + candidate ID. Mutations serialize through an immediate SQLite transaction and may change only review status plus external-research authorization; candidate value, kind, IDs and page/character provenance are immutable at this boundary. Promotion reloads current trusted state and reuses `promote_confirmed_identifier_candidate()` rather than accepting a client candidate object.

PR #64 exposes that mutation authority through authenticated, CSRF-protected HTTP actions. Confirm, reject, reopen and promote requests carry only artifact/candidate UUIDs. Review-state responses omit the candidate value; promotion returns a typed reviewed lead with artifact/page/character provenance but does not execute research. Audit events retain only bounded action/type metadata. CI also exposed and repaired an old dashboard test assumption that every FastAPI route-list entry had a `.path`; the runtime was not weakened to preserve that brittle assumption.

Remaining before V2-D closes:

1. define the explicit authenticated backend transition from a currently promoted/authorized document candidate into a chosen research/case run, without making promotion itself execute providers;
2. expose document review plus source-state/evaluation summaries cleanly to the private operator UI;
3. run a final catalog/binding/runtime/report/privacy/zero-spend consistency review;
4. close stale compatibility seams only where doing so does not break existing operator behavior or evidence semantics.

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

Add a separate private backend action that starts research from a currently confirmed, research-authorized upload candidate.

The action must not accept an arbitrary browser-supplied identifier as proof of review. It should reference artifact/candidate IDs, reload current server-owned state immediately before execution, require the existing authenticated write/CSRF boundary, enforce purpose/consent normally, and fail closed if the review record expired or authorization was revoked.

The resulting run/report must preserve reviewed-document artifact/candidate/page/character provenance without creating another raw-document store. Audit metadata must not duplicate identifier values. Confirmation and promotion remain state transitions only; provider traffic starts only through this separate explicit action.

After that, wire the review/run flow and existing source-state/evaluation summaries into the private operator UI, then run the final V2-D consistency review. Only then may new public/API sources be reviewed one at a time, with current official terms, authentication, limits and cost rechecked before activation.

Production recursion remains depth 2 / 12 nodes.

Success means the operator can answer for every hop:

> What source produced this clue, why was it allowed to become a lead, what did the system do with it, and what remains unknown?
