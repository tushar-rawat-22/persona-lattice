# PersonaLattice continuity

This is the current engineering handover for PersonaLattice. Read it before reconstructing old chats or making architectural changes. Current GitHub, provider and live evidence outrank historical notes.

## Repository authority

Repository: `tushar-rawat-22/persona-lattice`

Default branch: `main`

At this checkpoint, canonical `main` is `758b6ae3e96691e7f4880524e1ea49b826da0508`, merged through PR #344. Verify that SHA before acting because main can advance between runs. Exact-main CI is green on that release.

The current private-beta acceptance release is the same exact SHA: `758b6ae3e96691e7f4880524e1ea49b826da0508`. Operational rollback is `8b773b4dc1560ab1160f1a3ce30705f6a4bae179`; the runtime-manifest parent rollback is `4c0b05d4a0ae6215d8e1b884c78ef10f14432847`.

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

Cloudflare's deployment control plane currently reports successful deployment for exact main `758b6ae3e96691e7f4880524e1ea49b826da0508`. Treat that as deployment-identity evidence, not as a substitute for an independent live browser/HTTP reachability check.

Never place the authenticated private-beta hostname in README, repository profile text or marketing copy.

### Private beta

The current Mac-hosted private beta is under Issue #340 pre-external-operator acceptance on exact release `758b6ae3e96691e7f4880524e1ea49b826da0508`, with operational rollback `8b773b4dc1560ab1160f1a3ce30705f6a4bae179` and runtime-manifest parent rollback `4c0b05d4a0ae6215d8e1b884c78ef10f14432847`.

Tranche A is PARTIAL, not complete. Reuse passed proof while inputs remain unchanged: API/web loopback boundary, persistent SQLite invariants, Safari authentication, retained safe-case reopen, Chrome login, Chrome 390/320px rendering and keyboard focus have passed.

Remaining Tranche A work is MAC-DEPENDENT: complete and inspect one new bounded safe case; add an analyst decision and verify reload retention; search/reopen; synopsis/handoff; export/checksum review; logout denial and stale-UI behavior; restart, re-authenticate and prove case/decision/provenance persistence; authenticated Chrome journey; and the remaining Safari journey plus narrow viewport/keyboard checks.

External operator beta remains NO-GO until Issue #340 completes its A→B→C acceptance sequence and no unresolved P0/P1 defect remains.

PR #344 corrected a P1 deployment-contract defect exposed by Tranche A: the Git-tracked 0644 launchd preparation runner must be invoked through Bash rather than assumed executable. Future private-beta deployment preflight must explicitly verify executable-vs-interpreter invocation semantics before live bootstrap.

The Mac deployment is validation infrastructure. It is expected to be unavailable when the founder Mac sleeps and must never be described as always-on.

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

Issue #340 is the active company gate. #341/#339 visual differentiation is complete. Acceptance proceeds in bounded tranches A → B → C, and source expansion under Issue #222 must not outrun #340 when a source changes operator-visible behavior.

Tranche A is currently partial on exact release `758b6ae3e96691e7f4880524e1ea49b826da0508`. Stop after Tranche A closure; do not automatically begin Tranche B or #222 source expansion.

After Tranche A closes, Tranche B attacks degraded-source and evidence-integrity states: no-match, blocked/rate-limit/timeout/malformed/partial outage/all-unavailable, stale/duplicate/conflicting evidence, weak-vs-strong correlation and deliberate false-correlation/M5 semantics. Provider failure must never become identity evidence.

Tranche C then covers the remaining destructive/recovery/session/browser matrix and final external-operator GO/NO-GO evidence.

Do not continue UI polishing merely to generate PR count. The next product change should remove a concrete operator bottleneck or correctness ambiguity and must respect the active acceptance tranche.

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
- `docs/CURRENT_RELEASE_STATUS.md` — narrow current release/acceptance checkpoint;
- `docs/ROADMAP.md` — engineering sequence, but verify status against current GitHub before acting;
- Issue #340 — active pre-external-operator acceptance gate;
- Issue #222 — source admission/governance;
- source-admission records — exact provider contracts.

## Start-of-session procedure

Before changing code:

1. fetch current `main`;
2. identify the newest open implementation PR and exact head;
3. inspect exact-head CI and unresolved review threads;
4. verify the public observer separately when current deployment availability matters;
5. read Issue #340 for active acceptance authority and Issue #222 only for source work;
6. read the smallest implementation/deployment files needed for the active change;
7. ship the active bounded increment before opening an unrelated stream.

## Merge discipline

- keep each PR bounded;
- source expansion stays one source per PR;
- do not weaken a failing regression merely to obtain green CI;
- merge only after the exact unchanged head is fully green and review blockers are resolved;
- use an expected-head merge guard;
- while Tranche A is accepting exact release `758b6ae3e96691e7f4880524e1ea49b826da0508`, do not merge documentation-only work that would move canonical main unless the acceptance checkpoint is intentionally advanced;
- after merge, choose the next highest-value safe increment rather than manufacturing cosmetic churn.

## Immediate company-level priority

Close Issue #340 Tranche A on the exact private release without rerunning already-valid proof or allowing unrelated source/product work to move the acceptance target. Keep the public observer independent of founder hardware and the private runtime truthful about its Mac-dependent availability.

When local authenticated browser/runtime acceptance is blocked, continue only safe GitHub/cloud/provider/documentation/release-truth work that does not violate A→B→C sequencing. Do not weaken persistence, authentication, ingress, recovery or evidence semantics to obtain an always-on claim.

Do not repeat already-passed SQLite, browser, authentication or deployment checks unless relevant inputs change or a concrete defect appears. Every genuine runtime/browser/CI failure becomes the smallest regression/eval and, if the class repeats, a preflight/process correction rather than another symptom patch.
