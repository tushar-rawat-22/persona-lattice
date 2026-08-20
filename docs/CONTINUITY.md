# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent/review evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- Verified main before this block: `82ca5395899194a5be5afafbf9102a8b385109f4`
- PR #137: governed metadata-only RDAP activation — merged
- PR #138: bounded local consented M10 cohort runner — merged
- PR #139: independently reviewed M10 provenance boundary — merged
- PR #140: shared private local M10 materializer + reviewed runner — merged
- PR #142: operator DOMAIN research reachability — merged
- PR #144: operator pivot evidence context — merged
- PR #146: M5 operator factor explainability — merged at `82ca5395899194a5be5afafbf9102a8b385109f4`
- Issue #147: pre-DOMAIN SQLite identifier constraint upgrade — addressed by PR #148
- PR #148 implementation head before this documentation commit: `aee5d1cf25bd9fda785fdebaa36e51160665dc17`
- PR #148 implementation CI: run `32318068300`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- Current branch: `fix/sqlite-domain-identifier-migration`
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
- RDAP: active for explicit DOMAIN seeds through the governed runtime, PR #137; operator UI reachability complete in PR #142.
- Gravatar: PLANNED; blocked on provider privacy-policy/free-key requirements.
- WebFinger: PLANNED; parser/admission, SSRF transport, URL-only semantics and exact-host policy are complete, but no concrete host is approved.
- M10: deterministic replay, source/graph accounting, real-engine factor ablations, three-way label provenance (`synthetic`, `consented`, `independently_reviewed`), strict consented/reviewed-only accounting and shared private local cohort ingestion are implemented. Representative real evaluation remains incomplete.

## Latest block — SQLite DOMAIN upgrade path

RDAP made DOMAIN a canonical M1 identifier. New SQLite evidence stores therefore include `domain` in the `identifiers.kind` CHECK constraint, but an older persistent database keeps its original constraint because `create_all()` does not rewrite an existing SQLite table.

PR #148 adds migration `2026-08-20-domain-identifier-kind-v1`. Schema setup now checks existing SQLite identifier tables before normal metadata creation. The migrator accepts only the current constraint or the known pre-DOMAIN constraint; it also verifies the exact identifier-column layout, subject foreign key and subject/kind/comparison-key uniqueness contract. Unknown shapes fail closed with an operator-facing error.

For the known legacy shape, the migrator creates the current identifier table under a reserved temporary name, copies all rows, compares the copy in both directions, replaces the old table inside one `BEGIN IMMEDIATE` transaction, recreates the subject index and runs `PRAGMA foreign_key_check` before commit. SQLite foreign-key and legacy-alter settings are restored afterward. A forced mid-rebuild failure is regression-tested to roll the entire table replacement back.

The deterministic legacy fixture retains a subject, identifier, observation, claim, evidence link, correlation run and correlation factor. Tests prove those rows and identifier UUID references are unchanged after migration; DOMAIN is accepted afterward, unsupported identifier kinds remain rejected and a second migration run is a no-op. New databases remain on the normal current-schema path. Non-SQLite engines are skipped by the migration and continue through existing metadata creation.

The operator runbook now tells local users to stop the API and copy a persistent SQLite database before upgrading. Destructive reset is not the normal migration or recovery path.

The implementation head `aee5d1cf25bd9fda785fdebaa36e51160665dc17` passed the complete required CI matrix in run `32318068300`. This documentation commit must also pass the same matrix before merge.

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

1. Merge PR #148 only after the final documentation head passes the complete required CI matrix; Issue #147 should close with that merge.
2. Prioritize genuine consented or independently reviewed M10 evidence when lawful evidence exists. Do not invent a convenience cohort to claim evaluation progress.
3. Continue operator evidence/provenance work only where it removes a specific investigation step.
4. Add another external source only when it materially improves coverage and its current terms/privacy/cost/provenance boundary is defensible.
5. Keep production depth 2 / 12 nodes, M5 uncalibrated/non-probabilistic and `hard_contradiction` active.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
