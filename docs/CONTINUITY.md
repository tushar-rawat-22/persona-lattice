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
- PR #139: independently reviewed M10 label provenance and reviewed-only accounting — merged
- PR #139 exact tested head: `6ad918ee0a1cb1efdb405f905d11ab1c4cda3c48`
- PR #139 exact-head CI: run `32299192182`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
- PR #139 merge / verified main before the current block: `756e1459947bdd3ff75563474eb919d03bfb5885`
- Current branch: `m10-reviewed-local-runner`
- Current block: shared private local M10 cohort materializer + reviewed runner
- Current exact-head CI: pending; do not merge until the complete matrix passes
- Relevant decisions: ADR 0078 and ADR 0079
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
- RDAP: active for explicit DOMAIN seeds through the governed runtime, PR #137.
- Gravatar: PLANNED; blocked on provider privacy-policy/free-key requirements.
- WebFinger: PLANNED; parser/transport/URL-only semantics/exact-host policy exist, but no host is approved.
- M10: deterministic replay, graph/source accounting, real-engine factor ablations, three-way label provenance (`synthetic`, `consented`, `independently_reviewed`), consented/reviewed-only accounting and a local consented runner exist. Representative real evaluation remains incomplete.

## Current block — shared local evidence-backed cohort ingestion

PR #139 closed the semantic provenance gap: independently reviewed evidence now has its own basis and reviewed-only accounting boundary, while the consented-only boundary remains strict.

The next operational gap was that only consented evidence had a privacy-bounded local JSON runner. Duplicating that parser for reviewed evidence would create two normalization, graph-shape and privacy contracts, so this branch extracts one shared local cohort materializer.

The shared materializer keeps the existing limits and M1-backed canonicalization used by the consented runner. It builds the same `M10GraphFixture` contract and accepts the evidence basis only from the executable caller. Input JSON cannot select its own basis: top-level or fixture-level `basis` / `label_basis` fields are rejected.

The consented runner now calls the shared materializer with `CONSENTED`. A new reviewed runner calls it with `INDEPENDENTLY_REVIEWED`. Synthetic provenance is rejected by this evidence-backed local path.

Both runners:

- keep the 1 MiB input, 256-fixture and 2,048-node bounds;
- use the same production depth-2 / 12-node baseline and depth-3 / 12-node diagnostic candidate;
- require an opaque lowercase SHA-256 reference to the external consent/review record;
- require complete labels for admitted pivots at the matching analysis boundary;
- emit aggregate scenario accounting and experiment/provenance digests only;
- return generic CLI validation failures instead of echoing private values.

The two entry points stay separate intentionally. The operator chooses the evidence basis by choosing the consented or reviewed command, not through an input-file flag.

ADR 0079 records this design. `docs/M10_CONSENTED_COHORT_RUNBOOK.md` and `docs/M10_REVIEWED_COHORT_RUNBOOK.md` describe the two workflows.

## RDAP activation checkpoint

The live path remains:

`explicit DOMAIN seed → M1 DOMAIN normalization → rdap_domain_registry binding → DEVELOPMENT provider descriptor → process-wide ProviderRuntime → process-wide IANA bootstrap cache → SSRF-safe authoritative RDAP transport → metadata-only observation → typed source-run report → canonical converged evidence`

RDAP remains metadata-only. Registrant/contact names, organizations, addresses, email addresses and telephone numbers are excluded even when an upstream response contains them. No WHOIS fallback, RDRS/nonpublic lookup, reverse/bulk enumeration or contact harvesting is approved.

`routing_unavailable` remains a non-attempt outcome. Once an authoritative RDAP provider has actually been contacted, remote rate limits, transient failures and malformed returned results use attempted-failure semantics. Discovered domains remain `DISPLAY_ONLY`; only explicit DOMAIN seeds execute RDAP.

Existing persistent SQLite databases created before DOMAIN was added to the M1 enum constraint may require deliberate recreation/migration before persisting DOMAIN identifiers.

## Current controlled evaluation checkpoint

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

1. Put the current shared-materializer/reviewed-runner head through exact-head CI; repair any consented-runner regression instead of maintaining two parsers.
2. Merge only when API 3.11/3.13, audits/Ruff, web and production-image checks pass.
3. After merge, the M10 ingestion bottleneck is real evidence. Use the consented command only for genuine consent records and the reviewed command only for genuine independent review records.
4. Do not manufacture either evidence basis or publish population/calibration claims from a convenience cohort.
5. Add another external source only when it materially improves coverage and its current terms/privacy/cost/provenance boundary is defensible.
6. Keep production depth 2 / 12 nodes, M5 uncalibrated/non-probabilistic and `hard_contradiction` active.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
