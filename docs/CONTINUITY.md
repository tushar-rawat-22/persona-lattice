# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent/review evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- PR #137: governed metadata-only RDAP activation — merged
- PR #138: bounded local consented M10 cohort runner — merged
- PR #139: independently reviewed M10 provenance boundary — merged
- PR #140: shared private local M10 materializer + reviewed runner — merged
- PR #142: operator DOMAIN research reachability — merged
- PR #144: operator pivot evidence context — merged
- PR #146: M5 operator factor explainability — merged at `82ca5395899194a5be5afafbf9102a8b385109f4`
- PR #148: safe pre-DOMAIN SQLite identifier migration — merged at `4a686bf9d02c487c176d10087345ef1e58ee43c3`
- PR #148 exact tested final head: `60cd804416f82522e887e0d3993530f79cd59d26`
- PR #148 final CI: run `32318165893`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- Issue #147: closed as completed by PR #148
- PR #151: operator source-outcome explainability — merged
- PR #153: metadata-only retained-case index — merged at `24a3d7ee16a090b0e37c87067dc78f957423a5ba`
- PR #155: bounded older-case summary navigation — merged at `cd2c3986bc16366e6fc20840366db95afe0cc5d2`
- PR #157: latest-selection-wins retained-case loading — merged at `3a04a8c5fbc0d600ffc3df14551890590b35e9ef`
- PR #159: mutation-completion navigation reconciliation — merged at `bbe10dbd6a2dbc93ac92babc17f171f941134246`
- PR #159 exact tested final head: `e63ff281a007606bc4217ed9ff9678a0a2f063f4`
- PR #159 final CI: run `32344988541`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- Issue #158: closed as completed by PR #159
- PR #162: retained-case summary-page ordering — merged at `dd2d00bd069efa596724c19aca5922c44e8360df`
- PR #164: readable retained observation-field presentation — merged at `87edb016648a8017f7d7e16b2299239cd7ec85ad`
- PR #166: safe canonical web provenance links — open; exact-head CI required before merge
- Documentation standard: `docs/DOCUMENTATION_STANDARD.md`
- Zero-spend runbook: `docs/ZERO_SPEND_RUNBOOK.md`
- Optional paid Render reference: `deploy/render-paid.yaml`

## Milestone state

- M0-M6: complete.
- M7 private one-admin product: implemented and manually accepted locally.
- M8 privacy lifecycle/operations: substantially implemented.
- M9 private convergence: implemented.
- V2-A typed lead graph: complete, PR #20.
- V2-B deterministic frontier: complete, PR #21.
- V2-C source capability registry/planner: complete, PR #22.
- V2-D runtime consistency and architecture closure: complete, PRs #89-#90.
- Bluesky public profiles: active for valid AT handles, PR #98.
- RDAP: active for explicit DOMAIN seeds through the governed runtime, PR #137; operator UI reachability complete in PR #142; persistent pre-DOMAIN SQLite upgrade path complete in PR #148.
- Gravatar: PLANNED; blocked on provider privacy-policy/free-key requirements.
- WebFinger: PLANNED; parser/admission, SSRF transport, URL-only semantics and exact-host policy are complete, but no concrete host is approved.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, three-way label provenance (`synthetic`, `consented`, `independently_reviewed`), strict consented/reviewed-only accounting and shared private local cohort ingestion are implemented. Representative real evaluation remains incomplete.

## Retained-case navigation

The private console used `GET /v1/cases` only to render recent-case navigation, but that endpoint selected full rows and JSON-decoded every retained report. The browser then fetched the selected case again through `GET /v1/cases/{case_id}`. Raising the recent-case limit would therefore have increased personal-data deserialization and response payload without helping the investigation.

PR #153 replaces that list path with a dedicated summary projection. Storage selects only `id`, `created_at`, `expires_at`, `seed_kind` and `seed_value`; `report_json` is not selected or decoded. Results are bounded to 50 records per page and ordered by `(created_at DESC, id DESC)`. An opaque continuation cursor carries the final tuple, so records with identical timestamps remain deterministic.

The authenticated `GET /v1/cases` response contains navigation metadata only. When a next page exists the API returns `X-PersonaLattice-Next-Cursor`. `GET /v1/cases/{case_id}` remains the full-report read path, so evidence is loaded only when the operator opens a case. Existing delete, purge, expiry, audit and 30-day retention behavior is unchanged.

PR #155 completes the operator side of that continuation contract. Recent rows are typed as `StoredCaseSummary`, the console records the response cursor, and one compact `Load older cases` action requests the next eight summaries. Older pages append after deduplication by case ID. Create/delete/refresh returns the list to the newest page, and the active full report remains separate from the summary collection.

PR #157 orders retained-case reads explicitly in the browser. Each active-case context change advances a monotonic request generation. A full-case response or load error may update the visible case only while its generation is still current, so a slower response for an earlier click cannot replace a newer selection. Starting new research or a destructive case action invalidates pending case loads.

PR #159 separates that read-order rule from destructive mutation completion. A successful single-case delete, including idempotent 404, refreshes the metadata-only case index even if the operator selected another case while the DELETE was in flight. It uses the current active-case state when clearing the deleted case, so an older delete cannot erase a newer selection. Delete-all also refreshes summaries after success; it clears the active case only if its initiating context is still current. Failed deletes surface an error only while their initiating context remains current. The server-side mutation result is therefore reconciled without allowing stale reads or stale failures to overwrite newer evidence context.

Summary pagination has a separate monotonic generation from full-case selection. Starting a newest-page refresh invalidates continuation requests from the previous summary snapshot and clears that old continuation cursor while the refresh is in flight. An older-page response, failure or completion handler may append rows, replace the cursor or change the older-page loading state only while its summary generation is still current. This prevents a slow continuation request from reintroducing deleted/expired navigation rows or moving the browser back to a stale cursor after research, deletion or manual refresh has reconciled the newest page.

These are presentation-order guards only: full reports still come from the single-case endpoint, summary navigation stays metadata-only, and no retained evidence is duplicated or prefetched.

Regression coverage deliberately corrupts and enlarges a retained `report_json` value before listing summaries. The summary path must still work and must expose no report/evidence field. Additional tests cover bounded cursor pagination, invalid cursors/limits, authenticated summary response shape and the private web contract. UI contract tests lock summary typing, cursor consumption, duplicate suppression, no `item.report` access in navigation, full-case loading only from the single-case endpoint, stale retained-case response suppression, mutation reconciliation and stale summary-page suppression.

ADR 0080 records the metadata-index design. No retained database migration is required because the summary is projected from existing columns. The old full-report `CaseStore.list_recent()` method remains available for internal/historical compatibility but is not the operator navigation path.

## Operator observation-field presentation

PR #164 replaces raw-JSON-only observation reading with one shared read-only renderer for both converged and non-converged case paths. The operator still sees the canonical observation source, summary and source locator, but retained `Observation.details` fields are also presented directly as field/value rows so ordinary evidence inspection does not require scanning a JSON blob.

The renderer is deliberately provider-agnostic. String, number, boolean and null values are shown truthfully; arrays and objects use deterministic JSON with recursively sorted object keys while array order is preserved. Historical or unknown field names flow through the same `Object.entries()` path rather than depending on a provider-specific frontend schema.

Returned field values remain plain text. The browser does not auto-link URL-like strings and does not assign confidence, identity significance, lead eligibility or other research meaning. A collapsed `Raw retained JSON` disclosure keeps the exact retained payload available for audit/debug. This block adds no retained data and changes no provider, runtime, source-run, M5, recursion, RDAP, retention, authentication or CSRF behavior.

## Operator provenance links

PR #166 adds one shared renderer for canonical source locators shown in the private evidence view. It promotes only absolute `http://` and `https://` locators with a hostname and no embedded username/password to outbound links. Relative, malformed, credentials-bearing and non-web locators stay readable as plain text, which preserves historical and non-web provenance instead of treating every locator as a browser destination.

Link text is the retained locator itself. Web links open in a new tab with `noopener noreferrer`; the renderer does not rewrite the displayed provenance value. Reviewed seed provenance, M5 candidate provenance, pivot provenance, connected-field provenance and canonical observation locators use the same rule.

This is intentionally separate from retained observation fields. URL-looking strings inside `Observation.details` remain plain text and never pass through the source-locator renderer. The change adds no retained data and changes no provider, runtime, source-run, M5, recursion, RDAP, retention, authentication or CSRF behavior.

## Operator source-outcome explainability

The private case view retains typed source-run records and deterministic evaluation counters. PR #151 makes those counters readable without inventing a second policy layer: the operator can see neutral withheld reasons, attempted provider failures, routing/bootstrap unavailability, local budget stops, configuration gaps, policy blocks and non-executable planner states.

Attempt semantics stay explicit. Remote rate limits, execution failures and malformed results are labelled as provider-attempt failures. `routing_unavailable` is labelled `routing authority unavailable · no provider attempt`, preserving the RDAP bootstrap/routing contract instead of inflating provider failure counts. Historical retained cases without evaluation counters still fall back to the existing typed source-run view.

No source was activated, no provider/runtime semantics changed, no new retained personal data was added and no M5 or recursion policy changed in that block.

## SQLite DOMAIN upgrade path

RDAP made DOMAIN a canonical M1 identifier. New SQLite evidence stores include `domain` in the `identifiers.kind` CHECK constraint, but an older persistent database keeps its original constraint because `create_all()` does not alter an existing SQLite table.

PR #148 adds migration `2026-08-20-domain-identifier-kind-v1`. Schema setup checks existing SQLite identifier tables before normal metadata creation. The migrator accepts only the current constraint or the known pre-DOMAIN constraint; it also verifies the exact identifier-column layout, subject foreign key and subject/kind/comparison-key uniqueness contract. Unknown shapes fail closed with an actionable operator error.

For the known legacy shape, the migrator creates the current identifier table under a reserved temporary name, copies all rows, compares the copy in both directions, replaces the old table inside one `BEGIN IMMEDIATE` transaction, recreates the subject index and runs `PRAGMA foreign_key_check` before commit. SQLite foreign-key and legacy-alter settings are restored afterward. A forced mid-rebuild failure is regression-tested to roll the entire table replacement back.

The deterministic legacy fixture retains a subject, identifier, observation, claim, evidence link, correlation run and correlation factor. Tests prove those rows and identifier UUID references are unchanged after migration; DOMAIN is accepted afterward, unsupported identifier kinds remain rejected and a second migration run is a no-op. New databases remain on the normal current-schema path. Non-SQLite engines are skipped by the migration and continue through existing metadata creation.

The zero-spend operator runbook tells local users to stop the API and copy a persistent SQLite database before upgrading. Destructive reset is not the normal migration or recovery path.

## RDAP checkpoint

The live path remains:

`explicit DOMAIN seed → M1 DOMAIN normalization → rdap_domain_registry binding → DEVELOPMENT provider descriptor → process-wide ProviderRuntime → process-wide IANA bootstrap cache → SSRF-safe authoritative RDAP transport → metadata-only observation → typed source-run report → canonical converged evidence`

RDAP remains metadata-only. Registrant/contact names, organizations, addresses, email addresses and telephone numbers are excluded even when an upstream response contains them. No WHOIS fallback, RDRS/nonpublic lookup, reverse/bulk enumeration or contact harvesting is approved.

`routing_unavailable` remains a non-attempt outcome. Once an authoritative RDAP provider has actually been contacted, remote rate limits, transient failures and malformed returned results use attempted-failure semantics. Discovered domains remain `DISPLAY_ONLY`; only explicit DOMAIN seeds execute RDAP.

## M10 checkpoint

The two private evidence-backed entry points share one bounded local materializer. The consented command fixes provenance to `CONSENTED`; the reviewed command fixes it to `INDEPENDENTLY_REVIEWED`. Input JSON cannot promote its own evidence basis.

The runners keep the 1 MiB input, 256-fixture and 2,048-node bounds, M1-backed normalization, production depth-2 / 12-node baseline and depth-3 / 12-node diagnostic candidate. They emit aggregate accounting and cryptographic replay/provenance digests rather than raw private identifiers.

The engineering bottleneck is real lawful evidence, not another parser or synthetic metric.

## Controlled evaluation checkpoint

Production depth 2 / 12 nodes: 9 labelled admitted pivots (8 relevant, 1 wrong), 11 simulated attempts.

Candidate depth 3 / 12 nodes: 12 labelled admitted pivots (8 relevant, 4 wrong), 14 simulated attempts.

Controlled delta: +3 attempts, +3 wrong-labelled pivots, +0 relevant pivots. This is synthetic regression evidence only; production remains depth 2 / 12 nodes.

Controlled M5 omission results remain diagnostic only. `hard_contradiction` remains a production veto, M5 remains uncalibrated evidence-strength triage and `is_identity_claim=false` remains fixed.

## Permanent boundaries

- Required operation remains zero paid APIs, zero paid database, zero paid hosting requirement, zero paid proxy network and zero paid enrichment.
- Planned/review/manual/reference sources remain non-executable.
- Uploaded content is untrusted data; extraction is never execution authority.
- No private-account bypass, account-recovery enumeration, password/OTP/session/token collection, CAPTCHA/WAF/proxy/Tor evasion, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, covert subject contact or regulated eligibility decisioning.

## Next gate

1. Merge PR #166 only after its exact final head passes the complete required CI matrix; canonical web locators may be openable, but arbitrary retained field values must remain plain text.
2. Prioritize genuine consented or independently reviewed M10 evidence when lawful evidence exists. Do not invent a convenience cohort to claim evaluation progress.
3. Continue operator evidence/provenance work only where it removes a specific investigation step; do not recreate provider or M5 policy in the browser.
4. Add another external source only when it materially improves coverage and its current terms/privacy/cost/provenance boundary is defensible.
5. Keep production depth 2 / 12 nodes, M5 uncalibrated/non-probabilistic and `hard_contradiction` active.
6. Keep the SQLite DOMAIN migration regression green; never replace the versioned upgrade with a destructive reset shortcut.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
