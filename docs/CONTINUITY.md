# Continuity

This file is the handover for the next PersonaLattice engineering session. Read it before proposing work.

## Authoritative repository state

Repository: `tushar-rawat-22/persona-lattice`

Authoritative branch: `main`

Checkpoint before this freeze block: `06878baed0af883e51000d2b362328a19002d5dd` (`Record PR 166 merge checkpoint (#167)`).

At that checkpoint GitHub showed no open pull requests or issues. PR #166's exact tested head `37c6b95a1641ab8175cbfcad6a5ec59e3058fbca` passed CI run `32369415130` across Python 3.11, Python 3.13, dependency/Ruff checks, web audit/lint/typecheck/build and the production API image before merge.

## Engineering state

**The current private one-admin engineering foundation is complete.**

Do not interpret this as a population-validation claim. It means the repository-side completion gate is met and remaining product risk has moved to real evaluation evidence and source coverage.

Completed foundations:

- M0-M6: repository/CI, canonical evidence/provenance storage, deterministic normalization, bounded upload intake, provider governance, reviewed Sherlock discovery, deterministic M5 triage and the local evidence dashboard.
- M7-M9: deployment-configured one-admin authentication, Argon2 verification, HttpOnly sessions, CSRF, private `/admin`, same-origin API proxying, reviewed-document authority, retained cases, 30-day default expiry, explicit deletion and bounded live research.
- V2-A-D: typed leads/dispositions, exact-field extraction, deterministic frontier, source capability registry and full network-source migration behind the process-wide `ProviderRuntime`.
- DOMAIN/RDAP: canonical DOMAIN normalization and quick research, explicit-seed operator support, metadata-only RDAP through IANA bootstrap routing, non-attempt `routing_unavailable`, and a tested SQLite migration for pre-DOMAIN evidence stores.
- Operator correctness: metadata-only case listing, bounded cursor pagination, latest-selection-wins full-case reads, mutation/list reconciliation and stale-page suppression.
- Operator explainability: source-run outcome reasons, exact pivot source-field provenance, retained M5 factor rationale, readable observation fields and safe canonical provenance links. Browser code does not recreate source or M5 policy.
- M10 infrastructure: synthetic evaluation, depth-limit comparison, source accounting, replay fingerprints, M5 ablations, separate synthetic/consented/independently-reviewed provenance and private bounded runners for real consented or reviewed cohorts.

## Permanent boundaries

These are not cleanup items:

- Required spend stays ₹0. Paid or metered services may be optional only.
- Production convergence stays depth 2 / 12 nodes until real labelled evidence supports a change.
- M5 remains `calibration_status=uncalibrated` and `is_identity_claim=false`.
- `hard_contradiction` remains a production veto.
- No private-account bypass, credential/OTP/session-token collection, account-recovery probing, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, contact harvesting, WHOIS/RDRS nonpublic access, bulk/reverse enumeration or regulated eligibility decisioning.
- Canonical observations own provider source locators. Lead decisions and edges reference canonical provenance rather than duplicating it.
- Reviewed-document authority stays server-owned from extraction through explicit case execution.
- Historical retained cases remain read-only compatible; migrations must fail closed on unknown schema shapes.
- RDAP remains metadata-only. Discovered domain clues remain `DISPLAY_ONLY`.

## Active sources

Required/zero-direct-cost baseline:

- local normalization;
- libphonenumber metadata;
- reviewed Sherlock account discovery;
- GitHub public profile API;
- GitLab public profile API;
- Codeforces `user.info`;
- Bluesky public AppView profile lookup for valid AT handles;
- public DNS infrastructure metadata;
- authoritative RDAP for explicit DOMAIN seeds.

Optional:

- Brave exact public-web search when configured. It is metered and must never become a required dependency.

Planned/review-gated entries in the source catalog are not executable merely because code or a catalog record exists.

## M10 status

The repository-side M10 ingestion/evaluation path is ready. The blocker is real evidence.

Use `docs/M10_CONSENTED_COHORT_RUNBOOK.md` only when genuine consent records support the labels. Use `docs/M10_REVIEWED_COHORT_RUNBOOK.md` only when a real independent review record supports the labels. Do not convert repository fixtures, input flags or identifier hashes into either evidence basis.

Production depth 2 / 12 currently beats the depth-3 diagnostic candidate on the synthetic cohort: the deeper candidate adds attempts and wrong labelled pivots without additional relevant pivots. This is regression evidence only.

Do not publish false-positive/false-negative, probability, calibration or population-performance claims until cohort design and denominators support those terms.

## Source expansion transition

Source expansion is now the main engineering stream alongside real M10 evaluation. `docs/SOURCE_ADMISSION_QUEUE.md` records current preflight decisions.

The first implementation candidate is Internet Archive Wayback **availability metadata for exact URL leads only**. Current primary documentation confirms a URL availability endpoint and requires automated clients to identify themselves with a descriptive User-Agent and honor rate limiting. The intended PersonaLattice scope is metadata-only: capture availability/status/timestamp and the canonical Wayback snapshot locator. Do not fetch archived page content and do not emit new leads from this source.

Two tempting sources were rejected/deferred during the freeze review:

- ORCID Public API is not suitable for a future revenue-generating PersonaLattice baseline under its current public API terms.
- Stack Exchange `inname` user search is substring-based and is therefore too fuzzy to become generic recursive username evidence.

If the provider documentation changes, repeat the preflight instead of trusting this handover.

## Next engineering gate

1. Merge the engineering-freeze documentation only after exact-head CI is green.
2. Activate at most one external source per subsequent PR. For Wayback that means catalog → binding → DEVELOPMENT provider registry → process-wide `ProviderRuntime` → typed source-run accounting → canonical observation, with deterministic success/no-capture/malformed/rate-limit/unavailable tests.
3. Use a descriptive PersonaLattice User-Agent for Internet Archive automated requests and honor `429`/`Retry-After`.
4. Keep the Wayback adapter exact-URL and metadata-only; no archived content fetch, person attribution or emitted lead.
5. When genuine consented/reviewed M10 evidence exists, run it before changing production graph limits or M5 semantics.

Do not reopen completed architecture or generate cosmetic PRs simply to keep the repository moving. A new block needs to improve defensible source coverage, real evaluation, correctness, security or a concrete investigator task.