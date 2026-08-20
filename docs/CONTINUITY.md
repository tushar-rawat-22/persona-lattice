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
- PR #151: operator source-outcome explainability
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

## Latest block — operator source-outcome explainability

The private case view already retained typed source-run records and deterministic evaluation counters, but its summary exposed only attempts, completed/failed attempts, observations, no-match results, local budget stops and optional-source configuration. That forced the operator to inspect raw reason codes to answer a routine question: why is expected evidence missing?

PR #151 makes the retained counters readable without inventing a second policy layer. The view now surfaces non-zero neutral withheld reasons, attempted provider failures, routing/bootstrap unavailability, local budget stops, configuration gaps, policy blocks and non-executable planner states. It uses the retained evaluation projection directly and still ignores free-form warnings for source-state accounting.

Attempt semantics stay explicit. Remote rate limits, execution failures and malformed results are labelled as provider-attempt failures. `routing_unavailable` is labelled `routing authority unavailable · no provider attempt`, preserving the RDAP bootstrap/routing contract instead of inflating provider failure counts. Historical retained cases without evaluation counters still fall back to the existing typed source-run view.

No source was activated, no provider/runtime semantics changed, no new retained personal data was added and no M5 or recursion policy changed in this block.

## SQLite DOMAIN upgrade path

RDAP made DOMAIN a canonical M1 identifier. New SQLite evidence stores include `domain` in the `identifiers.kind` CHECK constraint, but an older persistent database keeps its original constraint because `create_all()` does not alter an existing SQLite table.

PR #148 adds migration `2026-08-20-domain-identifier-kind-v1`. Schema setup checks existing SQLite identifier tables before normal metadata creation. The migrator accepts only the current constraint or the known pre-DOMAIN constraint; it also verifies the exact identifier-column layout, subject foreign key and subject/kind/comparison-key uniqueness contract. Unknown shapes fail closed with an actionable operator error.

For the known legacy shape, the migrator creates the current identifier table under a reserved temporary name, copies all rows, compares the copy in both directions, replaces the old table inside one `BEGIN IMMEDIATE` transaction, recreates the subject index and runs `PRAGMA foreign_key_check` before commit. SQLite foreign-key and legacy-alter settings are restored afterward. A forced mid-rebuild failure is regression-tested to roll the entire table replacement back.

The deterministic legacy fixture retains a subject, identifier, observation, claim, evidence link, correlation run and correlation factor. Tests prove those rows and identifier UUID references are unchanged after migration; DOMAIN is accepted afterward, unsupported identifier kinds remain rejected and a second migration run is a no-op. New databases remain on the normal current-schema path. Non-SQLite engines are skipped by the migration and continue through existing metadata creation.

The zero-spend operator runbook tells local users to stop the API and copy a persistent SQLite database before upgrading. Destructive reset is not the normal migration or recovery path.

The exact final PR head `60cd804416f82522e887e0d3993530f79cd59d26` passed the complete required CI matrix in run `32318165893` before merge. PR #148 merged as `4a686bf9d02c487c176d10087345ef1e58ee43c3`, and Issue #147 closed as completed.

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

1. Prioritize genuine consented or independently reviewed M10 evidence when lawful evidence exists. Do not invent a convenience cohort to claim evaluation progress.
2. Continue operator evidence/provenance work only where it removes a specific investigation step. Source-run missing-evidence reasons are now directly readable from retained counters; do not recreate provider policy in the browser.
3. Add another external source only when it materially improves coverage and its current terms/privacy/cost/provenance boundary is defensible.
4. Keep production depth 2 / 12 nodes, M5 uncalibrated/non-probabilistic and `hard_contradiction` active.
5. Keep the SQLite DOMAIN migration regression green; never replace the versioned upgrade with a destructive reset shortcut.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
