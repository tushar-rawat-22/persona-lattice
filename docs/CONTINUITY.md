# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent/review evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- Verified main before this block: `4a92b661002d11a8e217c30460a9be3ff2f434e9`
- PR #137: governed metadata-only RDAP activation — merged
- PR #138: bounded local consented M10 cohort runner — merged
- Open PRs/issues before this block: none
- Current branch: `m10-reviewed-label-provenance`
- Current block: independently reviewed M10 label provenance and reviewed-only accounting
- Exact-head CI: pending; merge only after the complete required matrix passes
- Relevant decision: ADR 0078
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
- M10: deterministic replay, graph/source accounting, real-engine factor ablations, label-provenance manifests, consented-only accounting and a local consented cohort runner exist. Representative real evaluation remains incomplete.

## Current block — independently reviewed labels

The repository previously recognized only `synthetic` and `consented` M10 label provenance. That prevented a truthful analysis path for evidence established by independent review when consent was not the basis.

This branch adds `independently_reviewed` as a third explicit basis. The label manifest keeps fixture and declared-label counts for all three bases separately. The manifest still retains only an opaque lowercase SHA-256 reference to the external evidence/review record; raw identifiers, source documents, review notes and consent material stay outside Git.

A new reviewed-only analysis boundary accepts a cohort only when every fixture is `independently_reviewed`. It rejects synthetic, consented and mixed provenance, requires complete labels for every admitted pivot, and reports the same kind of exact scenario count fractions used by the consented analysis.

The reviewed fractions are descriptive within the reviewed corpus. They are not population false-positive/false-negative rates, calibration evidence, confidence or identity probability.

The existing consented-only analysis remains strict. Independently reviewed evidence does not satisfy its consent requirement.

ADR 0078 records the distinction and non-changes.

## RDAP activation checkpoint

The live path is:

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

1. Run exact-head CI for the reviewed-provenance branch; repair any regression rather than weakening the consent/review distinction.
2. Merge only when API 3.11/3.13, audits/Ruff, web and production-image checks are green.
3. Once merged, use the consented path only for genuine consent evidence and the reviewed path only for genuine independent review evidence. Neither path manufactures a real cohort.
4. Add another external source only if it has high coverage value and a defensible current zero-spend/terms/privacy/provenance story.
5. Keep production depth 2 / 12 nodes, M5 uncalibrated/non-probabilistic and `hard_contradiction` active.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
