# PersonaLattice continuity

This is the current engineering handover for PersonaLattice. Read it before reconstructing old chats or making architectural changes. Detailed historical decisions remain in Git history, merged pull requests, issues and `docs/decisions/`; this file intentionally stays focused on the state needed to continue correctly.

## Repository authority

Repository: `tushar-rawat-22/persona-lattice`

Default branch: `main`

The product baseline entering this documentation update is PR #307 merged as `d70341ae18de948d23203337b1bbcdf0c15875c4` on 2026-08-31. If `main` is newer, verify that it descends from this checkpoint and treat the current remote branch as authoritative.

Do not trust a remembered local SHA, old assistant message or historical section of a document over the current GitHub branch, current PR state and exact-head CI.

## Product state

PersonaLattice is a private-admin, evidence-first public-source research workbench with a live zero-secret public observer at `https://persona-lattice.pages.dev`. The public surface contains deterministic synthetic/demo material; real intake, provider execution and retained cases require the authenticated operator workflow.

The current private product is intentionally one admin, one API worker and SQLite-backed retained storage. That architecture is valid for the private operator product and private beta. It is not yet a multi-user SaaS architecture.

Permanent boundaries:

- observations, source claims and correlation decisions remain separate;
- every retained observation keeps attributable provenance;
- M5 remains uncalibrated and non-probabilistic and never becomes an identity probability;
- hard contradictions remain visible and can veto positive evidence;
- a discovered identifier is a research lead, not proof that two records belong to one person;
- no private-account bypass, credential/OTP/token collection, hidden KYC/government-ID acquisition, contact harvesting, covert personal/device IP discovery, live tracking, broad ownership traversal, reverse/bulk enumeration or regulated eligibility decisioning;
- provider execution fails closed on policy, routing, configuration, budget and malformed-result boundaries.

## Launch state

`LAUNCH_CANDIDATE_1` is complete. Issue #218 closed on 2026-08-27 after software, host and browser evidence was recorded.

The exact host/browser-tested LC1 commit is `18b6b75b7dc28d3883752aec013911223726423c`. Exact-commit post-merge CI was run `33008932692` / CI #2226 and passed. The private host evidence summary is outside Git at:

`$HOME/Library/Application Support/PersonaLattice/lc1/20260826T200923Z.json`

That session covered production preflight, same-origin web/API routing, authentication/CSRF, exact URL/domain research, source-state/provenance/M5 contracts, reviewed-document promotion, retained-case operations, restart persistence, SQLite backup/restore, session invalidation, logout, log privacy and Safari/Chrome acceptance.

LC1 is a software + real-host launch candidate. It is not the stable private-beta endpoint.

The zero-secret public observer is live at `https://persona-lattice.pages.dev`. It was created on 2026-08-31 from the canonical repository using `apps/web`'s dedicated `build:public-demo` static export. Founder live smoke screenshots verified the public overview and synthetic evidence workspace. The public `Private admin` path intentionally resolves to the safe operator-access boundary; no admin login, private API URL, provider execution, retained-case mutation or credentials belong in the Pages deployment.

The one-admin private-beta launch gate was proven GREEN on 2026-09-02 against exact release `6bcb51aa5c3ad9e5c7da4352b9a3308d64ada31e`, with rollback `01ebf5ca8968f3cc2cd31ce54204a9ee76571627`. The ingress is an account-assigned development-tier HTTPS tunnel on a zero-cost plan and publishes only the loopback web origin; the API remains loopback-only behind the same-origin web proxy. Real-host evidence covers protected persistent SQLite, backup and isolated restore, app and ingress restart persistence, anonymous denial, login/logout, secure-cookie behavior, current-token CSRF mutation, the unchanged missing/stale-token negative CSRF contract, one bounded research case, retained-case reopen, Safari, Chrome, narrow viewport and keyboard navigation. Owner-only runtime and ingress configuration remains outside Git. Availability still depends on the founder Mac staying awake and online, and the development-tier ingress has provider limits/interstitial behavior; this is private-beta evidence, not a claim of commercial production hosting. `authority_effect=NONE`.

The private hostname, credentials and host-local evidence are intentionally not recorded in Git.

For the current public/private operating split and deployment contract, read `docs/LIVE_BETA.md` before creating new deployment architecture.

## Active engineering stream

The private-beta launch gate is green. The primary company-level engineering objective is now the authenticated operator product: remove concrete friction from clue → evidence → source state → provenance → contradiction/uncertainty → operator decision while preserving the existing public/private and evidence-integrity boundaries.

Issue #252 remains the operator-workspace product-quality stream for concrete usability/correctness bottlenecks. Deployment work should re-enter NOW only when fresh host/provider evidence shows regression or when uptime, scale, compliance or cost justifies a hosting change.

Major post-LC1 improvements already merged include:

- compact authenticated application bar;
- explicit corroborated/conflicting/open-question decision surface;
- searchable/filterable/sortable retained-case navigation;
- one-action provenance disclosure and safe canonical-locator copy;
- decisive M5 factor summaries with explicit truncation disclosure;
- retained source-execution state summaries that distinguish failed, withheld, not-attempted and no-match states;
- inline confirmation for single and bulk case deletion;
- stale retention-deadline handling without inventing server deletion state;
- explicit expired-session handling and fail-closed remote actions;
- distinct initial loading, failed-index and confirmed-empty case states;
- `/` shortcut for retained-case search;
- `N` shortcut for reopening New intake;
- explicit retained evidence paths in Graph;
- factor-first public M5 interpretation;
- reviewed-document workflow simulation in the public observer;
- retained-case navigation simulation in the public observer.

Do not continue UI polishing merely to generate PR count. The next product change should remove a concrete operator bottleneck or correctness ambiguity.

## Source governance

Issue #222 is the governing zero-spend source admission matrix. Its body was corrected after LC1 to remove the obsolete pre-LC1 freeze. Source work remains one source per PR and requires current primary-source terms/privacy/auth/rate-limit/contact-risk review before activation.

Community OSINT directories are candidate indexes only. They never authorize execution against every listed site.

Two important post-LC1 corrections to older handovers:

- GLEIF exact LEI is active. PR #245 merged as `f7a7b19e31bc86d70a2c2e9dc4de1c42730bebdb`. It accepts only an exact canonical GLEIF LEI record URL, validates the identifier locally, performs a bounded exact lookup, retains narrow legal-entity registry metadata, emits no recursive leads and keeps `identity_claim=false`.
- SEC EDGAR exact CIK is active through the governed runtime and Quick Research. PR #254 merged as `ef0dcecf7fa8438ca869f80a43b395655ebf5ee0`. It accepts only the exact canonical submissions URL shape, performs one bounded submissions request, retains narrow filer metadata, emits no recursive leads and keeps `identity_claim=false`. `SEC_EDGAR_USER_AGENT` is required non-secret operator configuration and must fail before network contact when absent.

If an older file or issue comment says those sources are still deferred, that statement is historical and no longer authoritative.

Other active exact/bounded source families include reviewed Sherlock username discovery, GitHub, GitLab, Keybase, Bluesky, local phone metadata, public DNS infrastructure metadata, Wayback availability, exact Stack Overflow profiles, OpenAlex when configured, Wikidata, Zenodo, ROR, Companies House when configured, DBLP, Crossref/DataCite DOI handling and public RDAP. The source admission records and current provider/catalog/binding/runtime code are authoritative for exact applicability and retained fields.

Do not broaden an exact source into fuzzy person search, account enumeration, contact enrichment, private data, content scraping or ownership traversal because the upstream API supports it.

## Runtime architecture

Browser → Next.js web → same-origin `/api/*` proxy → FastAPI API.

The API owns authentication, CSRF validation, provider governance/execution, evidence normalization/correlation and retained cases.

Current production constraints:

- exactly one API worker/replica because session records are process-local;
- SQLite database must live on protected persistent storage;
- secure `__Host-personalattice_session` cookie on HTTPS;
- provider credentials/operator metadata remain server-side;
- optional provider configuration must degrade to typed unavailable/not-configured states rather than fabricate evidence.

Primary deployment documentation: `docs/DEPLOYMENT.md` and `docs/LIVE_BETA.md`.

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
- `docs/LIVE_BETA.md` — current live/demo/private-beta operating choices;
- `SECURITY.md` and `THIRD_PARTY.md` — security and external-license/integration boundaries.

AI/maintainer continuity:

- this file — current authoritative handover;
- `docs/ROADMAP.md` — engineering sequence, but verify its status lines against current GitHub before acting;
- Issue #222 — source admission/governance;
- Issue #252 — current operator-product quality stream;
- source admission records — exact provider contracts.

Public docs should read like ordinary maintainer documentation, not assistant transcripts. Continuity may be dense and operational because its job is to prevent context reconstruction.

## Start-of-session procedure

A new assistant/model should do only this before changing code:

1. fetch current `main`;
2. identify the newest open implementation PR and exact head;
3. inspect exact-head CI and unresolved review threads;
4. verify the live public observer only if deployment state is relevant;
5. read Issue #222 only if source work is relevant, and Issue #252 only if operator-product work is relevant;
6. read the smallest implementation/deployment files needed for the active PR;
7. fix/ship the active bounded increment before opening another unrelated stream.

Do not spend the first several prompts replaying old history. Use this file to establish architecture and boundaries, then verify only the state that can have changed.

## Merge discipline

For normal implementation work:

- keep each PR bounded;
- source expansion stays one source per PR;
- do not weaken a failing regression simply to obtain green CI;
- merge only after the exact unchanged head is fully green and review blockers are resolved;
- use an expected-head merge guard;
- after a merge, choose the next highest-value safe increment rather than manufacturing cosmetic churn.

## Immediate company-level priority

Keep the proven one-admin private beta operational while improving the operator workflow itself. The highest-value next changes should reduce context loss, make evidence/source-state/provenance/uncertainty easier to interpret, or remove a verified case-navigation friction point without broadening collection authority.

The development-tier HTTPS ingress is sufficient for the current one-admin beta while its observed limits remain acceptable. Do not buy or migrate hosting merely for hostname aesthetics. Revisit hosting only when uptime, scale, compliance, provider limits or cost evidence makes the current founder-Mac architecture materially inadequate.

Do not repeat already-passed SQLite, backup/restore, restart, authentication or browser acceptance work unless relevant inputs change or a concrete defect appears. Keep public observer parity through deterministic sanitized fixtures when private concepts change, and never couple the public Pages observer to the private API.
