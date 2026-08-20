# Continuity

This file is the handover for the next PersonaLattice engineering session. Read it before proposing work.

## Authoritative repository state

Repository: `tushar-rawat-22/persona-lattice`

Authoritative branch: `main`

Engineering-freeze baseline: PR #168, merged as `5d774a9fadc336d43e06491183d9035d016db04f` after exact-head CI passed.

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

## Active sources in the current code state

Required/zero-spend baseline:

- local normalization;
- libphonenumber metadata;
- reviewed Sherlock account discovery;
- GitHub public profile API;
- GitLab public profile API;
- Codeforces `user.info`;
- Bluesky public AppView profile lookup for valid AT handles;
- public DNS infrastructure metadata;
- Internet Archive Wayback capture-availability metadata for canonical URLs;
- Stack Overflow exact public-profile metadata for explicit numeric profile URLs;
- OpenAlex exact-author metadata when a free server-side key is configured;
- authoritative RDAP for explicit DOMAIN seeds.

Optional:

- Brave exact public-web search when configured. It is metered and must never become a required dependency.

Wayback is intentionally metadata-only. It queries the official availability endpoint, sends a descriptive PersonaLattice User-Agent, validates the returned `web.archive.org` snapshot locator, and retains only queried URL plus capture availability/status/timestamp. It does not fetch archived page content, emit leads or make a person-attribution claim. Provider rate limits and malformed outputs stay visible through typed source-run reporting.

Stack Overflow is exact-URL account metadata only. Applicability requires a supplied `stackoverflow.com/users/<positive-id>` profile URL; the provider then calls the official exact-user API. It retains only prefixed user ID/display name/reputation/creation metadata, API attribution, `identity_claim=false`, and the canonical returned profile locator. It does not retain profile prose, posts/comments, location, website, image or contact fields, and it emits no leads. Generic Stack Exchange `inname` user search remains outside the product.

OpenAlex is exact-author-URL metadata only. Applicability requires `https://openalex.org/A<positive-digits>` with no credentials, port, query or fragment. The provider calls only the official singleton author endpoint and retains author ID, display name, works count, cited-by count, CC0 attribution and `identity_claim=false`. It does not retain ORCID/Scopus/MAG identifiers, affiliations, locations, topics, alternative names, publications, full text or contact fields and emits no leads. The free key stays server-side in `OPENALEX_API_KEY` and is sent as bearer authorization, never in a URL. Missing key is `credential_not_configured` with no provider attempt. A returned author ID mismatch fails closed rather than silently switching scholarly identities.

Planned/review-gated entries in the source catalog are not executable merely because code or a catalog record exists.

## M10 status

The repository-side M10 ingestion/evaluation path is ready. The blocker is real evidence.

Use `docs/M10_CONSENTED_COHORT_RUNBOOK.md` only when genuine consent records support the labels. Use `docs/M10_REVIEWED_COHORT_RUNBOOK.md` only when a real independent review record supports the labels. Do not convert repository fixtures, input flags or identifier hashes into either evidence basis.

Production depth 2 / 12 currently beats the depth-3 diagnostic candidate on the synthetic cohort: the deeper candidate adds attempts and wrong labelled pivots without additional relevant pivots. This is regression evidence only.

Do not publish false-positive/false-negative, probability, calibration or population-performance claims until cohort design and denominators support those terms.

## Source expansion state

Source expansion is the main engineering stream alongside real M10 evaluation. `docs/SOURCE_ADMISSION_QUEUE.md` records current preflight decisions.

Wayback was the first post-freeze source admission. Its contract is exact-URL historical availability metadata only. Treat zero capture as a valid no-match, `429` as a remote rate limit, malformed provider output as a post-attempt validation failure, and transient provider/network failure as unavailable. The source emits no recursive candidates.

Stack Overflow is the second admitted post-freeze source. Its applicability boundary is an exact profile URL with a numeric user ID, not a username/display-name query. Anonymous requests use the official Stack Exchange API, stay under a conservative local budget, preserve provider `Retry-After`/API `backoff`, and keep Stack Overflow attribution visible with canonical provenance.

OpenAlex is the next admitted source in this code state. Its applicability is an exact author entity URL, not a person-name search. Current primary documentation was re-checked on 2026-08-21: API keys are required and free, bearer authentication is supported, singleton-by-ID retrieval is a free operation, author names are not safe identifiers, and the data is CC0. Re-check those provider facts before future source-policy changes.

Current explicit rejections/deferments include:

- ORCID Public API is not suitable for a future revenue-generating PersonaLattice baseline under its current public API terms.
- Hacker News public-user metadata is rejected under current Y Combinator commercial-use terms despite a technically attractive free API.
- Stack Exchange `inname` user search is substring-based and therefore too fuzzy to become generic recursive username evidence; this does not affect the exact Stack Overflow profile-URL source.

If provider documentation changes, repeat the preflight instead of trusting this handover.

## Next engineering gate

1. Keep Wayback, Stack Overflow and OpenAlex source boundaries/tests green; do not expand them into content scraping, fuzzy person search or hidden identity reconciliation.
2. Review the next high-value ₹0 source from primary documentation before writing an adapter. Reject sources whose terms, privacy model or matching semantics do not fit the product even if the endpoint is free.
3. When genuine consented/reviewed M10 evidence exists, run it before changing production graph limits or M5 semantics.
4. Fix concrete correctness/security/operator defects as discovered; do not reopen frozen architecture or create cosmetic PRs to simulate progress.

A new block must improve defensible source coverage, real evaluation, correctness, security or a concrete investigator task.
