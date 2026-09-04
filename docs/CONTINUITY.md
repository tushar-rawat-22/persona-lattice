# PersonaLattice continuity

This is the current engineering handover for PersonaLattice. Read it before reconstructing old chats or making architectural changes. Current GitHub, provider and live evidence outrank historical notes.

## Repository authority

Repository: `tushar-rawat-22/persona-lattice`

Default branch: `main`

At this checkpoint, canonical `main` is `ad467d249402fbbf6300a06713b8e29b7739bed0`, merged through PR #327. Verify that SHA before acting because main can advance between runs. Exact-main CI #2907 passed on that release.

Do not trust a remembered local SHA, old assistant message or historical section over the current GitHub branch, current PR state and exact-head CI.

## Product state

PersonaLattice is a private-admin, evidence-first public-source research workbench with a zero-secret public observer at `https://persona-lattice.pages.dev`. The public surface contains deterministic synthetic/demo material only; real intake, provider execution and retained cases require the authenticated operator workflow.

The private product intentionally remains one admin, one API worker and SQLite-backed retained storage. That architecture is valid for the current private operator product. It is not a multi-user SaaS architecture.

Permanent boundaries:

- observations, source claims and correlation decisions remain separate;
- every retained observation keeps attributable provenance;
- M5 remains uncalibrated and non-probabilistic and never becomes an identity probability;
- hard contradictions remain visible and can veto positive evidence;
- a discovered identifier is a research lead, not proof that two records belong to one person;
- no private-account bypass, credential/OTP/token collection, hidden KYC/government-ID acquisition, contact harvesting, covert personal/device IP discovery, live tracking, broad ownership traversal, reverse/bulk enumeration or regulated eligibility decisioning;
- provider execution fails closed on policy, routing, configuration, budget and malformed-result boundaries.

## Reliability matrix

### Public observer

The canonical public observer is the static Cloudflare Pages deployment at `https://persona-lattice.pages.dev`. It must remain synthetic, sanitized, read-only and independent of the founder Mac, ngrok, localhost, private API, retained cases and credentials.

The dedicated public build lives under `apps/web` and uses the `build:public-demo` static export. CI verifies the public boundary and public-demo artifact. A green artifact proves the repository export boundary; live-host reachability should still be checked separately when making a current availability claim.

Never place the authenticated private-beta hostname in README, repository profile text or marketing copy.

### Private beta

The accepted Mac-hosted private beta is GREEN on exact release `369378a8d2401c6f8a1322929c530909aa5123c8`, with rollback `7a124d73da9bf82979ecc8032464502f123b74f2`, based on the accepted 2026-09-03 changed-surface deployment evidence.

That release passed the macOS release-verifier regression, retained server search/reopen with safe fallback, persistence, anonymous denial/admin login, API loopback-only boundary, Chrome/Safari quick smoke and exact live release identity. Its HTTPS validation ingress publishes only the loopback web origin; the API remains loopback-only behind the same-origin web proxy.

The Mac deployment is validation infrastructure. It is expected to be unavailable when the founder Mac sleeps and must never be described as always-on.

GitHub main has advanced beyond that deployed release through retained-case cursor scope binding, the provider-neutral Linux deployment bundle, a privacy-bounded retained-case analyst synopsis and public reliability documentation. Batch the next Mac acceptance rather than forcing a deploy for every merge.

Private always-on hosting is NOT YET ESTABLISHED.

## Zero-cash infrastructure policy

Current founder spend is zero. Do not recommend, request or activate:

- paid hosting, database or storage;
- a purchased domain;
- a billing-enabled service;
- a card-required signup;
- a VM, object store, database or API subscription that can incur charges.

OCI Always Free is a future option only if the founder later changes the no-card/no-billing-activation policy. Oracle's current Free Tier signup documentation requires valid credit/debit-card information and can use temporary authorization holds, so OCI signup is not a current action and is not a blocker.

The same rule applies to every alternative provider. A nominally free tier does not qualify as a current action if account creation requires a card or billing activation.

If no truly no-card, hard-free persistent host satisfies the current security and storage contracts, keep the private beta local rather than weakening persistence, authentication, ingress or recovery.

## Provider-neutral Linux deployment bundle

`deploy/linux/` prepares the current one-admin architecture for a small persistent Linux host later without creating provider authority now. The bundle must preserve:

- exact-SHA release preparation and rollback identity;
- one dedicated runtime user;
- owner-only configuration outside Git;
- persistent protected SQLite storage;
- systemd restart persistence;
- one web origin;
- API loopback-only isolation;
- health and release verification;
- integrity-checked backup/restore;
- optional web-only Cloudflare Tunnel ingress with unmatched routes failing closed.

Do not add provider-specific deployment logic merely to make a future signup easier. The deployment contract should remain portable.

## Active engineering stream

The private-beta launch gate is green. The primary engineering objective is the authenticated analyst product: remove concrete friction from clue → evidence → source state → provenance → contradiction/uncertainty → operator decision while preserving the public/private and evidence-integrity boundaries.

Issue #252 is the operator-workspace product-quality stream. Major post-LC1 improvements already merged include:

- compact authenticated application bar;
- explicit corroborated/conflicting/open-question decision surface;
- searchable/filterable/sortable retained-case navigation;
- pagination cursors bound to normalized active search/filter scope;
- one-action provenance disclosure and safe canonical-locator copy;
- decisive M5 factor summaries with explicit truncation disclosure;
- retained source-execution state summaries that distinguish failed, withheld, not-attempted and no-match states;
- inline confirmation for single and bulk case deletion;
- stale retention-deadline handling without inventing server deletion state;
- explicit expired-session handling and fail-closed remote actions;
- distinct initial loading, failed-index and confirmed-empty case states;
- retained evidence paths in Graph;
- privacy-bounded retained-case analyst synopsis/handoff;
- reviewed-document and retained-case workflow simulation in the public observer.

Do not continue UI polishing merely to generate PR count. The next product change should remove a concrete operator bottleneck or correctness ambiguity.

## Source governance

Issue #222 is the governing zero-spend source-admission matrix. Source work remains one source per PR and requires current primary-source terms/privacy/auth/rate-limit/contact-risk review before activation.

Community OSINT directories are candidate indexes only. They never authorize execution against every listed site.

Active exact/bounded source families include reviewed Sherlock username discovery, GitHub, GitLab, Keybase, Bluesky, local phone metadata, public DNS infrastructure metadata, Wayback availability, exact Stack Overflow profiles, OpenAlex when configured, Wikidata, Zenodo, ROR, Companies House when configured, DBLP, Crossref/DataCite DOI handling, GLEIF, SEC EDGAR and public RDAP. The source-admission records and current provider/catalog/binding/runtime code are authoritative for exact applicability and retained fields.

Do not broaden an exact source into fuzzy person search, account enumeration, contact enrichment, private data, content scraping or ownership traversal because the upstream API supports it.

## Runtime architecture

Browser → Next.js web → same-origin `/api/*` proxy → FastAPI API.

The API owns authentication, CSRF validation, provider governance/execution, evidence normalization/correlation and retained cases.

Current production constraints:

- exactly one API worker/replica because session records are process-local;
- SQLite must live on protected persistent storage;
- secure `__Host-personalattice_session` cookie on HTTPS;
- provider credentials/operator metadata remain server-side;
- optional provider configuration must degrade to typed unavailable/not-configured states rather than fabricate evidence.

SQLite remains the private-beta store until measured concurrency, tenancy, query or HA requirements justify Postgres or another storage architecture. Do not move retained state onto an ephemeral free filesystem simply to obtain hosted compute.

## Required configuration

Core authenticated runtime:

- `PERSONALATTICE_ADMIN_USERNAME`
- `PERSONALATTICE_ADMIN_PASSWORD_HASH`
- `PERSONALATTICE_DB_PATH`
- `PERSONALATTICE_COOKIE_SECURE=true` for HTTPS
- `PERSONALATTICE_SESSION_COOKIE=__Host-personalattice_session`

Optional/current provider configuration includes `BRAVE_SEARCH_API_KEY`, `OPENALEX_API_KEY`, `COMPANIES_HOUSE_API_KEY` and `SEC_EDGAR_USER_AGENT` where those sources are enabled/applicable.

Never place real secrets, the retained database, private evidence, production logs containing sensitive payloads or host acceptance evidence into Git.

## Documentation split

Human/public documentation:

- `README.md` — product, capabilities, boundaries and repository entry point;
- `docs/PRODUCT_CHARTER.md` — product intent and scope;
- `docs/ARCHITECTURE.md` — system design;
- `docs/DEPLOYMENT.md` — deployment architecture/configuration;
- `docs/LIVE_BETA.md` — public/private operating choices and release gate;
- `docs/hosted-zero-spend.md` — zero-cash hosting constraints and provider-neutral migration path;
- `SECURITY.md` and `THIRD_PARTY.md` — security and external-license/integration boundaries.

Maintainer continuity:

- this file — current authoritative handover;
- `docs/ROADMAP.md` — engineering sequence, but verify status against current GitHub before acting;
- Issue #222 — source admission/governance;
- Issue #252 — current operator-product quality stream;
- source-admission records — exact provider contracts.

## Start-of-session procedure

Before changing code:

1. fetch current `main`;
2. identify the newest open implementation PR and exact head;
3. inspect exact-head CI and unresolved review threads;
4. verify the public observer separately when current deployment availability matters;
5. read Issue #222 only for source work and Issue #252 only for operator-product work;
6. read the smallest implementation/deployment files needed for the active change;
7. ship the active bounded increment before opening an unrelated stream.

## Merge discipline

- keep each PR bounded;
- source expansion stays one source per PR;
- do not weaken a failing regression merely to obtain green CI;
- merge only after the exact unchanged head is fully green and review blockers are resolved;
- use an expected-head merge guard;
- after merge, choose the next highest-value safe increment rather than manufacturing cosmetic churn.

## Immediate company-level priority

Keep the public observer independent of founder hardware, keep the accepted one-admin private beta useful, and improve analyst decision efficiency while the private always-on hosting question remains intentionally unresolved under the no-card/no-billing policy.

Continue provider-neutral Linux preparation and recovery contracts, but do not request any provider signup. Evaluate a truly no-card, hard-free host only if it offers durable persistent storage and can preserve exact release identity, protected SQLite, loopback API isolation, restart persistence, backup/restore and stable HTTPS ingress. Otherwise stay local.

Do not repeat already-passed SQLite, backup/restore, restart, authentication or browser acceptance work unless relevant inputs change or a concrete defect appears. Keep public observer parity through deterministic sanitized fixtures when private concepts change, and never couple the public Pages observer to the private API.
