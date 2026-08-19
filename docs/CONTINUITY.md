# Continuity

Public-safe engineering handover for PersonaLattice. Verify GitHub before changing anything; this file is a checkpoint, not authority over the repository.

Never place API keys, real research identifiers, retained-case data, password hashes, session material, raw consent evidence or unredacted investigation screenshots here.

## Repository checkpoint

- Repository: `tushar-rawat-22/persona-lattice`
- Default branch: `main`
- Local checkout convention: `~/persona-lattice`
- License: Apache-2.0 for original code
- Operating model: one authenticated operator; public route is demo/preview only
- Verified main before the current M10 block: `e14167efcdc65582eac75c960bb71a4a7757cf03`
- PR #137: governed metadata-only RDAP activation — merged
- Issue #133: closed; DOMAIN reachability and routing-accounting blockers are complete
- Current implementation branch: `m10-local-consented-cohort-runner`
- Current PR: #138 — local bounded consented M10 cohort runner
- Exact tested implementation head before this continuity checkpoint: `e3bac8f4886d7e7ad35c5118a100249fabe09e6e`
- Exact-head CI: run `32294421695`; API 3.11 PASS, API 3.13 PASS, web PASS, deployment-image PASS
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
- M10: deterministic replay, graph/source accounting, real-engine factor ablations, label-provenance manifests and consented-only accounting exist. Representative consented evaluation remains incomplete.

## RDAP activation checkpoint

The live path is:

`explicit DOMAIN seed → M1 DOMAIN normalization → rdap_domain_registry binding → DEVELOPMENT provider descriptor → process-wide ProviderRuntime → process-wide IANA bootstrap cache → SSRF-safe authoritative RDAP transport → metadata-only observation → typed source-run report → canonical converged evidence`

RDAP remains metadata-only. Registrant/contact names, organizations, addresses, email addresses and telephone numbers are excluded even when an upstream response contains them. No WHOIS fallback, RDRS/nonpublic lookup, reverse/bulk enumeration or contact harvesting is approved.

`routing_unavailable` remains a non-attempt outcome. Once an authoritative RDAP provider has actually been contacted, remote rate limits, transient failures and malformed returned results use attempted-failure semantics. Discovered domains remain `DISPLAY_ONLY`; only explicit DOMAIN seeds execute RDAP.

Existing persistent SQLite databases created before DOMAIN was added to the M1 enum constraint may require deliberate recreation/migration before persisting DOMAIN identifiers.

## Current M10 block — local consented cohort runner

M10 already had consented-only scenario accounting, but real consented cohorts still required hand-written Python fixtures. PR #138 closes that operational gap without committing private identifiers.

The runner reads a private local JSON file and materializes the existing `M10GraphFixture` contract. It does not create a second frontier evaluator or scoring path. Identifiers pass through the existing M1-backed lead normalization, and the resulting fixture cohort goes through the existing replay and consented-analysis builders.

The provenance vocabulary currently distinguishes `synthetic` from `consented` only. PR #138 therefore accepts **consented evidence only**. Independently reviewed-but-not-consented evidence must not be relabelled as consented; supporting that later requires a separate provenance basis and analysis contract.

Current bounds:

- input file: at most 1 MiB;
- fixture count: at most 256;
- declared node count: at most 2,048;
- each fixture requires an opaque lowercase SHA-256 reference to an external consent record;
- children may only descend from the seed or an earlier successful automatic pivot;
- admitted pivots must have complete relevance labels before consented analysis succeeds.

The CLI output contains aggregate scenario accounting and digests only. It does not echo seed values, lead values, source locators, fixture names, the cohort name or raw external consent evidence. The cohort name is represented by a digest. Validation failures return one generic message so underlying canonicalization/fixture exceptions cannot leak private values to terminal error output.

The runner compares the current production depth-2 / 12-node policy against the existing depth-3 / 12-node diagnostic candidate. It does not change production limits.

ADR 0077 documents this boundary. `docs/M10_CONSENTED_COHORT_RUNBOOK.md` describes the local file contract and invocation.

The exact implementation head `e3bac8f4886d7e7ad35c5118a100249fabe09e6e` passed CI run `32294421695` completely. The current continuity-only head must pass the same required matrix before PR #138 merges.

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

1. The continuity-only PR #138 head must pass exact-head CI before merge.
2. Once merged, M10 has a practical local path for real **consented** labels. The unresolved bottleneck becomes the actual lawful consented cohort, not ingestion code.
3. Do not manufacture progress by relabelling synthetic or merely reviewed fixtures as consented. Run the local tool only when an external consent record genuinely supports each fixture label.
4. Add another source only if it has high coverage value and a defensible current zero-spend/terms/privacy/provenance story.
5. Keep production depth 2 / 12 nodes, M5 uncalibrated/non-probabilistic and `hard_contradiction` active.

## Update discipline

For every meaningful block record verified main/branch/PR state, CI evidence, behavior changes, explicit non-changes, corrected assumptions, unresolved risks and the exact next gate. Keep public/operator prose separate from assistant handover prose.
