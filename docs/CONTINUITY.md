# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent/review evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- Verified main before this block: `9b167653fb92e2d2ae50d8a2df2ba5b08e535b01`
- PR #137: governed metadata-only RDAP activation — merged
- PR #138: bounded local consented M10 cohort runner — merged
- PR #139: independently reviewed M10 provenance boundary — merged
- PR #140: shared private local M10 materializer + reviewed runner — merged at the verified main above
- Open product bug at block start: Issue #141 — operator UI omitted live DOMAIN research
- Current branch: `fix/domain-operator-research`
- Current block: expose explicit DOMAIN research in the private operator UI and lock backend/UI research-kind parity
- Current exact-head CI: pending; merge only after the complete required matrix passes
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
- M10: deterministic replay, graph/source accounting, real-engine factor ablations, three-way label provenance (`synthetic`, `consented`, `independently_reviewed`), strict consented/reviewed-only accounting, and shared private local cohort ingestion are implemented. Representative real evaluation remains incomplete.

## Current block — operator DOMAIN research reachability

RDAP became live for explicit DOMAIN seeds in PR #137, but the private `QuickResearch` component still exposed only username, phone, email and URL. The backend capability therefore existed without a normal operator entry point. Issue #141 correctly treated that as a product bug rather than a cosmetic request.

This branch adds `domain` to the web `ResearchKind` contract and starting-identifier selector, keeps the existing `/v1/cases/run-converged` request body unchanged, and gives domain input the bare-domain example `example.com`.

The UI states the policy boundary directly: domain research is explicit-seed only. Domain clues discovered during another case remain `DISPLAY_ONLY`; this block does not add domain auto-pivoting or alter recursion policy.

A cross-layer regression test now imports the live backend `ResearchKind` enum and compares it with both the TypeScript research-kind union and the selector option set. A future backend kind addition or UI refactor therefore fails CI if the operator surface silently loses an executable research kind.

Stored DOMAIN cases require no separate rendering branch. They use the existing retained-case header, research-node kind/value display, typed source-run summary, canonical observation source locators and recent-case list. The regression contract explicitly checks those paths remain present.

No new network provider, RDAP field, permission, retention field or evidence semantic is added here.

## RDAP checkpoint

The live path remains:

`explicit DOMAIN seed → M1 DOMAIN normalization → rdap_domain_registry binding → DEVELOPMENT provider descriptor → process-wide ProviderRuntime → process-wide IANA bootstrap cache → SSRF-safe authoritative RDAP transport → metadata-only observation → typed source-run report → canonical converged evidence`

RDAP remains metadata-only. Registrant/contact names, organizations, addresses, email addresses and telephone numbers are excluded even when an upstream response contains them. No WHOIS fallback, RDRS/nonpublic lookup, reverse/bulk enumeration or contact harvesting is approved.

`routing_unavailable` remains a non-attempt outcome. Once an authoritative RDAP provider has actually been contacted, remote rate limits, transient failures and malformed returned results use attempted-failure semantics. Discovered domains remain `DISPLAY_ONLY`; only explicit DOMAIN seeds execute RDAP.

Existing persistent SQLite databases created before DOMAIN was added to the M1 enum constraint may require deliberate recreation/migration before persisting DOMAIN identifiers.

## M10 checkpoint

The two private evidence-backed entry points share one bounded local materializer. The consented command fixes provenance to `CONSENTED`; the reviewed command fixes it to `INDEPENDENTLY_REVIEWED`. Input JSON cannot promote its own evidence basis.

The runners keep the 1 MiB input, 256-fixture and 2,048-node bounds, M1-backed normalization, production depth-2 / 12-node baseline and depth-3 / 12-node diagnostic candidate. They emit aggregate accounting and cryptographic replay/provenance digests rather than raw private identifiers.

The engineering bottleneck is now real lawful evidence, not another parser or synthetic metric.

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

1. Put the DOMAIN operator branch through exact-head CI and repair any web/API regression rather than weakening the parity contract.
2. Merge only when API 3.11/3.13, audits/Ruff, web and production-image checks pass; close Issue #141 with the merge.
3. After that, prioritize real consented/reviewed M10 evidence and operator evidence/provenance usability. Do not invent a convenience cohort to claim evaluation progress.
4. Add another external source only when it materially improves coverage and its current terms/privacy/cost/provenance boundary is defensible.
5. Keep production depth 2 / 12 nodes, M5 uncalibrated/non-probabilistic and `hard_contradiction` active.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
