# Roadmap

PersonaLattice is a private, evidence-first research workbench. The public route is a demo surface; real research, provider execution and retained cases belong to the authenticated operator workflow.

## Permanent product rules

- Keep observations, factual claims and correlation results separate.
- Keep provenance for every retained observation, admitted lead and triage result.
- Treat a lead as a research direction, not proof that two records belong to the same person.
- M5 stays uncalibrated and non-probabilistic. `hard_contradiction` remains a production veto.
- Keep production convergence at depth 2 / 12 nodes until real labelled evidence supports a change.
- No biometric identity model, private-account bypass, credential/account-recovery probing, hidden KYC/government-ID acquisition, covert personal/device IP discovery, live tracking, contact harvesting or regulated eligibility decisioning.
- The required operating baseline stays ₹0: no paid API, hosting, database, proxy or enrichment dependency.

## Engineering foundation

**Complete as of 2026-08-20.**

The completion gate is met for the current private one-admin product:

- M0-M6 evidence, provenance, normalization, provider governance and local dashboard are complete.
- M7-M9 authentication, CSRF, private operator flow, reviewed document intake, retained cases, expiry/delete controls and bounded live research are implemented.
- V2-A through V2-D typed leads, deterministic frontier, source capability registry and ProviderRuntime consistency are complete.
- Every active explicit research kind is reachable from the operator UI, including explicit DOMAIN research.
- Retained-case listing is metadata-only and cursor-bounded; full evidence loads only when one case is opened. Open/delete/list ordering regressions cover stale asynchronous responses.
- Operator views expose retained observation fields, source-run outcomes, exact pivot provenance and retained M5 factor rationale without recreating provider or M5 policy in the browser.
- Historical SQLite evidence stores have a tested, idempotent DOMAIN migration; current schemas are left unchanged and unknown schemas fail closed.
- The local one-admin baseline runs without a paid service. `docs/ZERO_SPEND_RUNBOOK.md` is the authoritative zero-spend operating path.
- Current required CI covers Python 3.11/3.13, dependency and lint checks, web lint/typecheck/build and the production API image.

This is an engineering freeze, not a claim that PersonaLattice is validated in the population. New engineering work should now be justified by source coverage, real M10 evidence, a concrete correctness defect or a specific operator investigation bottleneck. Do not keep polishing completed foundations because there is spare implementation time.

## Active source baseline

Current executable sources are:

- reviewed Sherlock username discovery;
- GitHub public profiles from exact username seeds or exact canonical public profile URLs plus exact public repository metadata through one shared provider budget;
- GitLab public profiles from exact username/public-email seeds or exact canonical public profile URLs plus exact subgroup-aware public project metadata through one shared provider budget;
- Keybase public account basics for already-canonical Keybase usernames;
- Bluesky public profiles for valid AT handles;
- local phone numbering-plan metadata;
- public DNS infrastructure metadata;
- Internet Archive Wayback capture-availability metadata for canonical URLs;
- Stack Overflow public-account metadata for exact numeric profile URLs;
- OpenAlex scholarly-profile metadata for exact author URLs when a free server-side key is configured;
- Wikidata CC0 entity metadata for exact item URLs;
- Zenodo CC0 record metadata for exact canonical record URLs;
- ROR CC0 organization metadata for exact canonical ROR URLs;
- Companies House public-register company metadata for exact canonical company URLs when a free server-side key is configured;
- DBLP CC0 person metadata for exact canonical person PID URLs;
- Crossref bibliographic metadata for exact DOI resolver URLs;
- DataCite CC0 DOI metadata as a fallback only after a clean Crossref no-match;
- authoritative metadata-only RDAP for explicit DOMAIN seeds;
- optional Brave exact public-web search when configured.

Codeforces is deferred/non-executable after PR #209. Current Codeforces terms did not establish a defensible commercial SaaS reuse basis for the public profile metadata, so central policy blocks it before provider contact while historical evidence remains readable.

GitHub username, exact profile-URL and repository lookup share the same process-owned `github_public_api` adapter and the same 50-request/hour local budget. Exact profile URL applicability requires canonical `https://github.com/<login>` with one non-empty path segment, no credentials, custom port, query or fragment, and no known reserved GitHub root route. Profile URLs reuse official `GET /users/{username}`; exact login consistency, `type=User` and a canonical returned `html_url` remain mandatory. Repository applicability is only an exact `https://github.com/<owner>/<repo>` URL with no credentials, custom port, query, fragment or extra route. The repository path calls only official `GET /repos/{owner}/{repo}` and retains the canonical full name, owner login/type, explicit public-state check and bounded fork/archived flags. It does not retain descriptions, contents, popularity counters, issues, contributors or contact-like fields. Repository-owner login is display-only because owners can be organizations; repository observations emit no leads.

GitLab username, exact public-email, exact public-profile URL and exact public-project lookup share the same process-owned `gitlab_public_api` adapter and the same 20-request/minute local budget. Profile applicability accepts only canonical `https://gitlab.com/<username>` with one non-empty segment and rejects credentials, custom ports, query/fragment, percent-encoded paths, `/-/u/<id>` and documented reserved top-level routes. Profile URLs reuse the human-only username lookup; a one-segment group namespace therefore produces a clean no-match rather than a person inference. Returned profile username and canonical `web_url` must match the supplied username. Project applicability accepts exact canonical `https://gitlab.com/<namespace...>/<project>` paths with at least two non-empty segments. Local admission rejects credentials, custom ports, query/fragment, `.git`, empty or malformed `.`/`-` segments, organization-scoped `/o/...` routes and GitLab `/-/` action routes. The provider calls only official `GET /api/v4/projects/{URL-encoded full project path}` and requires `visibility=public`, exact full `path_with_namespace`, namespace `full_path` matching every namespace segment before the project name, and an exact canonical returned `web_url`. Retained project fields remain provider-specific display context and emit no leads. Username/public-email/profile-URL requests retain GitLab's documented `humans=true` filter.

Keybase runs only when the normalized username is already valid in Keybase's public namespace: 2-16 lowercase alphanumeric/underscore characters with an alphanumeric first character. The adapter requests only the API `basics` object and retains username, public UID, account creation timestamp and canonical profile provenance. It does not request profile text, proofs, external identities, public keys, cryptocurrency addresses or contact-like material. It emits no leads; a same-handle result remains an account candidate rather than an identity claim.

Wayback retains capture metadata only. It fetches no archived page content, emits no new leads and makes no person-attribution claim.

Stack Overflow runs only when an already-supplied URL matches an exact `stackoverflow.com/users/<id>` profile. It uses the official exact-user API endpoint, retains a narrow attributed account-metadata record and emits no leads. Generic Stack Exchange `inname` search remains rejected because substring display-name matching is too ambiguous for identity evidence.

OpenAlex runs only when the supplied URL is exactly an `openalex.org/A<id>` author entity. It calls the official singleton author endpoint with a free server-side key, retains only author ID, display name, works/citation counts, CC0 attribution and `identity_claim=false`, and emits no leads. Name/ORCID search, affiliations, topics and work expansion are deliberately excluded. Missing key is a non-attempt configuration state.

Wikidata runs only for an exact `www.wikidata.org/wiki/Q<id>` item URL. It uses official `wbgetentities` reads and retains only the QID plus bounded English label/description metadata, CC0 attribution and `identity_claim=false`. It does not request structured claims, aliases, sitelinks, external identifiers or linked entities. The optional description remains bounded public descriptive text and is never parsed into identity claims or recursive leads.

Zenodo runs only for an exact canonical `https://zenodo.org/records/<positive-id>` URL. It performs one credentialless official singleton record read and retains only the canonical record ID, one bounded title, CC0/CERN attribution, canonical provenance and `identity_claim=false`. It does not search, resolve DOI-like text, fetch files, traverse versions, request restricted content, or retain descriptions, creators, ORCID/affiliations, communities, grants, related identifiers, uploader data or geolocation. It emits no leads. PersonaLattice stays at one attempt, one concurrency slot, four seconds, 30 requests/minute and a 32 KiB raw-response ceiling; oversized records fail closed rather than expanding the adapter boundary.

ROR runs only when the supplied URL is an exact canonical `https://ror.org/<id>` organization identifier. It calls the official credentialless v2 singleton organization endpoint and retains only the canonical ROR ID, one bounded `ror_display` name, active record status, bounded organization types when present, CC0 attribution and `identity_claim=false`. Search, affiliation matching, autocomplete, external-ID expansion, domains, links, aliases, relationships, locations/geocodes and contact-like fields are excluded. Provider-specific retained field names keep the display name out of generic lead extraction, and the source emits no leads.

Companies House runs only when the supplied URL is an exact canonical public company page. It calls the official exact company-profile endpoint using a free server-side `COMPANIES_HOUSE_API_KEY` via HTTP Basic authentication. Retained evidence is limited to company number, bounded registered name/status/type, an optional valid incorporation date, public-register attribution and `identity_claim=false`. Registered-office addresses, officers/directors/secretaries/PSCs, person names, SIC/business descriptions, accounts/confirmation data, insolvency/charges, filings/documents, previous names and jurisdiction/location expansion are excluded. Missing key is a non-attempt configuration state and the source emits no leads.

DBLP runs only when the supplied URL is an exact canonical `https://dblp.org/pid/<pid>` person identifier. It sends one minimal exact-resource query to DBLP's public SPARQL service and retains only the canonical PID URL, one bounded `primaryCreatorName`, CC0 attribution and `identity_claim=false`. It does not use DBLP name search, bibliography exports, publication/coauthor expansion, affiliations, ORCID/external IDs or homepages. The provider-specific name field remains display-only and emits no leads. The source is credentialless and locally capped at one concurrency slot and six requests/minute because DBLP's public SPARQL service is shared beta infrastructure.

Crossref runs only for an exact `https://doi.org/<doi>` URL. It uses the official anonymous singleton `GET /works/{doi}` path, retains the DOI, one bounded title, an optional publication year and up to eight bounded author display names with `identity_claim=false`, and emits no leads. Author names are display context only. Crossref search/list operations, abstracts, author IDs/ORCIDs, affiliations, references, funders and full-text/resource expansion are excluded.

DataCite uses the same exact DOI URL applicability but is not a second parallel DOI query. It runs only when Crossref completes normally with zero observations. A Crossref timeout, rate limit, malformed result or other attempted failure blocks fallback so the original source failure remains visible. DataCite retains only DOI, one bounded title, optional publication year/resource type, up to eight display-only creator names, CC0 attribution and `identity_claim=false`; it performs no search or relation expansion and emits no leads.

RDAP emits no subject leads. Registrant/contact fields are not admitted. Discovered domain clues remain `DISPLAY_ONLY`; only explicit DOMAIN seeds run RDAP.

Brave remains optional and metered. It is not part of the required ₹0 baseline.

## Source expansion

Source expansion is now the primary engineering stream alongside real M10 evaluation.

Every external source must pass a fresh preflight from primary provider documentation immediately before activation. The preflight must cover current terms/data-use rules, authentication, quota/backoff, returned fields, contact risk, retention implications, operational stability and actual cost.

Community API directories and GitHub lists are discovery indexes only. They are not evidence that a provider permits PersonaLattice use.

Activation follows the existing path:

`catalog → binding → DEVELOPMENT provider registry → process-wide ProviderRuntime → typed source-run reporting → canonical evidence`

Activate at most one external source per PR. A source must degrade through typed unavailable/rate-limited/not-applicable outcomes rather than weakening the rest of the investigation pipeline.

Current source-admission decisions are tracked in `docs/SOURCE_ADMISSION_QUEUE.md`; source-specific admission records may add implementation detail without replacing that queue.

### GitHub exact public repository

**Active through the existing GitHub provider.**

Only an exact canonical `https://github.com/<owner>/<repo>` URL is applicable. Username-profile research and repository metadata use the same provider descriptor, adapter instance and 50-request/hour local budget; adding the repository path does not create another GitHub quota pool. GitHub currently documents 60 unauthenticated REST requests/hour per originating IP.

The repository adapter calls only official `GET /repos/{owner}/{repo}`. It requires the response to be explicitly public and to match the requested full name, owner and canonical locator. Retained evidence is limited to repository full name, owner login, bounded owner type, explicit `private=false`, optional fork/archived booleans, canonical repository URL and `identity_claim=false`. Search, contents, contributors, commits, issues, releases, popularity counters and contact-like fields are outside the source. Repository fields emit no leads.

The detailed admission record is `docs/source-admissions/GITHUB_EXACT_REPOSITORY.md`.

### GitLab exact public project

**Active through the existing GitLab provider.**

Exact canonical `https://gitlab.com/<namespace...>/<project>` URLs are applicable, including subgroup namespaces. Username, exact public-email and project lookup share one provider descriptor, one process-owned adapter and the same 20-request/minute local budget. Local applicability rejects credentials, custom ports, query/fragment, `.git`, empty or malformed `.`/`-` segments, organization-scoped `/o/...` routes and GitLab `/-/` action routes.

The project adapter calls only official unauthenticated `GET /api/v4/projects/{URL-encoded full project path}`. It requires `visibility=public`, exact full-path agreement, namespace `full_path` matching every namespace segment before the project name, and an exact canonical GitLab `web_url`. Retained evidence is limited to numeric project ID, exact project path, public visibility, bounded namespace kind/full path, optional archived flag, canonical locator and `identity_claim=false`. Search, repository contents, owner/member enumeration, contributors, commits, issues/MRs, releases, branches/tags, pipelines/jobs, packages, popularity counters and contact-like fields are outside the source. Project fields emit no leads.

The detailed admission record is `docs/source-admissions/GITLAB_EXACT_PROJECT.md`.

### Keybase public account basics

**Active.**

The source accepts only already-canonical Keybase usernames. PersonaLattice does not lowercase, trim into, or otherwise coerce a generic username into Keybase's provider namespace. Noncanonical usernames are not applicable and cause no Keybase provider attempt.

The official credentialless lookup is called with `fields=basics`. Retained evidence is limited to exact username, public UID, account creation timestamp, canonical profile locator, `account_candidate=true` and `identity_claim=false`. Profile data, proofs, linked external identities, public keys, cryptocurrency addresses and contact-like data are outside this source. No recursive leads are emitted.

Keybase's API documentation describes the API as evolving/alpha, so response shape and exact returned username/UID are validated fail-closed. PersonaLattice adds its own 4-second timeout, 16 KiB response ceiling, one-concurrency budget and 20-request/minute local rate budget even though no provider quota is relied on for the zero-spend contract.

### Internet Archive Wayback

**Active.**

The integration uses the official availability endpoint for exact canonical URL leads. Automated requests identify PersonaLattice with a descriptive User-Agent and map provider `429` responses through typed remote-rate-limit handling. Returned snapshot locators must be credential-free HTTP(S) URLs on `web.archive.org` with a timestamp-consistent archive path.

The adapter stores only queried URL, capture availability/status/timestamp and canonical snapshot provenance. It never fetches archived page content and intentionally emits no recursive leads.

### Stack Overflow exact public profile

**Active.**

The source parses an exact Stack Overflow profile URL locally, extracts the numeric user ID and calls the official Stack Exchange API v2.3 `/users/{id}` path for `site=stackoverflow`. It does not call `/users?inname=` or perform display-name search.

Retained fields are intentionally narrow: Stack Overflow user ID, public display name, reputation, creation timestamp, explicit API attribution, `identity_claim=false`, and the canonical returned profile locator. `about`, posts/comments, location, website, profile image and contact fields are not admitted. No recursive leads are emitted.

Anonymous API reads keep the source at zero direct cost. PersonaLattice applies a tighter local rate budget than the provider's documented quota and honors remote `429`/`Retry-After` plus API `backoff` signals.

### OpenAlex exact author

**Active when configured.**

The source admits only an exact HTTPS OpenAlex author URL with an `A<positive-digits>` ID. It uses the official singleton-author API call with `Authorization: Bearer <OPENALEX_API_KEY>` and never places the key in a request URL. Current OpenAlex documentation describes the key as free and singleton-by-ID retrieval as a free operation; those provider facts must be re-checked before future release changes.

Retained evidence is limited to the canonical author ID, public display name, works count, cited-by count, CC0 attribution and `identity_claim=false`. No ORCID/Scopus/MAG IDs, affiliations, locations, topics, alternative names, publications, abstracts/full text or contact data are admitted. No recursive leads are emitted.

A missing key is reported as `credential_not_configured` before a provider attempt. If the returned author ID differs from the exact ID requested, the result fails closed rather than silently following a merged/reassigned scholarly identity.

### Wikidata exact entity

**Active.**

The source admits only an exact HTTPS Wikidata item URL with a `Q<positive-digits>` ID. It uses the official Wikibase Action API `wbgetentities` operation with the exact QID and requests English labels/descriptions only. Current Wikidata policy makes structured item data CC0.

Retained evidence is limited to the canonical QID, bounded English label/description when present, CC0 attribution and `identity_claim=false`. Structured claims, aliases, sitelinks, external IDs and linked entities are not requested or admitted. The optional English description can contain ordinary public biographical wording, but PersonaLattice does not parse that prose into dates, locations, occupations, organizations, identity claims or recursive leads.

The source is credentialless and zero-direct-cost. Requests carry a meaningful PersonaLattice User-Agent, use a one-concurrency local budget of 30 requests/minute, send `maxlag=5`, and preserve provider `429`/`Retry-After`. API-level `ratelimited` and `maxlag` errors map to typed rate/backoff outcomes. Returned entity-ID mismatch, non-item results and malformed provider data fail closed rather than silently changing entity context.

### Zenodo exact record

**Active.**

The source admits only an exact canonical HTTPS Zenodo record URL under `/records/<positive-id>`. It performs one credentialless `GET /api/records/<id>` singleton read. Zenodo's current public-record API permits anonymous metadata access and metadata are CC0 by default.

Retained evidence is limited to the canonical record ID, one title capped at 512 characters, `data_license=CC0`, Zenodo/CERN attribution, canonical record locator and `identity_claim=false`. Search, DOI guessing, descriptions, creators, ORCID/affiliations, files/checksums, communities, grants, related identifiers, geolocation, uploader/account data, restricted-content workflow and version traversal are excluded. No leads are emitted.

PersonaLattice keeps one attempt, one concurrency slot, a 4-second timeout, 32 KiB raw-response ceiling and 30-request/minute local budget, below Zenodo's current guest record-service allowance. `404` is a completed no-match; `429` preserves valid `Retry-After`; 408/5xx/network failures remain attempted unavailable states; malformed, oversized or mismatched record IDs fail closed.

The detailed admission record is `docs/source-admissions/zenodo-exact-record.md`.

### ROR exact organization

**Active.**

The source admits only an exact canonical HTTPS ROR organization URL. The provider calls official `GET /v2/organizations/{id}` without credentials; organization-name search, affiliation matching, autocomplete, reverse lookup and bulk enumeration remain outside PersonaLattice.

Retained evidence is limited to the canonical ROR ID, exactly one bounded `ror_display` name, `active` record status, up to eight bounded organization types when present, CC0 attribution and `identity_claim=false`. External IDs, domains, links, aliases beyond the chosen display name, relationships, locations/addresses/geocodes, search candidates and contact-like fields are excluded. No recursive leads are emitted.

ROR's current documentation announces a future unidentified tier of 50 requests per five minutes. PersonaLattice stays below that with one attempt, one concurrency slot, a 4-second timeout, 32 KiB response ceiling and local eight-request/minute budget. `404` is a completed no-match; `429` preserves `Retry-After`; transient failures remain attempted unavailable outcomes; malformed, non-active or mismatched records fail closed.

### Companies House exact company

**Active when configured.**

The source admits only an exact canonical `https://find-and-update.company-information.service.gov.uk/company/<company-number>` URL. It calls official `GET /company/{company_number}` using `COMPANIES_HOUSE_API_KEY` as the HTTP Basic username with a blank password. It does not use company-name, officer/PSC or alphabetical search and does not traverse filings/documents.

Retained evidence is limited to company number, one bounded registered company name, bounded status/type, an optional valid incorporation date, Companies House public-register attribution and `identity_claim=false`. Registered-office addresses, officers/directors/secretaries/PSCs, person names, SIC/business descriptions, accounts/confirmation fields, insolvency/charges, filing history/document links, previous names, jurisdiction/location expansion and contact-like data are excluded. No recursive leads are emitted.

Companies House documents free public API access and a default provider limit of 600 requests per five minutes. PersonaLattice stays far below that with one attempt, a 4-second timeout, 32 KiB response ceiling, one concurrency slot and 30 requests/minute. A missing key is `credential_not_configured` before any provider attempt; `404` is no-match; `401`/`403` are attempted credential failures; `429` preserves `Retry-After`; transient failures stay attempted unavailable; malformed or mismatched company records fail closed.

### DBLP exact person PID

**Active.**

The source admits only an exact canonical HTTPS DBLP person URL under `/pid/`. DBLP's persistent PIDs are case-sensitive identifiers; PersonaLattice preserves the supplied case and does not infer a PID from a name. The provider sends one minimal SPARQL query constrained to that exact resource and the `dblp:Person` class, returning only the resource plus `dblp:primaryCreatorName`.

Retained evidence is limited to the canonical PID URL, one bounded primary creator name, CC0 attribution and `identity_claim=false`. The source performs no author-name search and does not fetch publication bibliographies, coauthors, affiliations, ORCID/external IDs, homepages or contact-like data. `dblp_primary_name` is provider-specific display context and emits no recursive lead.

The source is credentialless and zero-direct-cost. Because DBLP describes the public SPARQL service as beta and rate-limited against aggressive scripting, PersonaLattice uses one attempt, a 4-second timeout, 32 KiB response ceiling, one concurrency slot and a six-request/minute local budget. Empty results are no-match; `429` preserves `Retry-After`; transient failures stay attempted unavailable; returned-resource mismatch or non-unique/malformed primary-name results fail closed.

### Crossref exact work

**Active.**

The source admits only an exact HTTPS DOI resolver URL with a syntactically valid DOI. It calls the official public singleton `GET /works/{doi}` endpoint without credentials. It never calls Crossref search, query, filter, cursor or list operations.

Retained evidence is limited to the canonical DOI, one bounded title, a valid publication year when present, up to eight bounded author display names, Crossref attribution and `identity_claim=false`. Author display names are not admitted as leads. Abstracts, ORCID/other author IDs, affiliations, references, funders, subjects, relation/update expansion and full-text/resource links are excluded.

Crossref says almost all deposited bibliographic metadata can be reused for any purpose, while abstracts may remain subject to publisher or author copyright. The source excludes abstracts and does not treat a full provider response as reusable content. PersonaLattice adds a 4-second timeout, 32 KiB adapter response ceiling, one-concurrency budget and 30-request/minute local rate budget. `404` is a completed no-match; `429` preserves `Retry-After`; transient failures are attempted unavailable states; malformed or returned-DOI-mismatch results fail closed.

### DataCite exact DOI fallback

**Active after a clean Crossref no-match.**

DataCite is a fallback for the same explicit `https://doi.org/<doi>` seed, not an additional discovery search. PersonaLattice calls the public singleton `GET /dois/{id}` endpoint without credentials only when Crossref completed successfully with zero observations. If Crossref was unavailable, rate-limited or malformed, DataCite does not run and cannot mask that attempted failure.

Retained DataCite evidence is limited to canonical DOI, one bounded title, valid publication year/resource type when present, up to eight bounded creator display names, `data_license=CC0`, DataCite attribution and `identity_claim=false`. Creator names are display-only and never become pivots. Name identifiers/ORCID, affiliations, descriptions, geolocations, funding, related identifiers, subjects, rights/resource links and usage/activity fields are excluded. The source emits no leads.

The source uses one attempt, a 4-second timeout, 32 KiB adapter ceiling, one-concurrency execution and a local 30-request/minute budget, well below DataCite's current unidentified public tier. `404` is a completed no-match, `429` preserves `Retry-After`, transient network/5xx failures remain attempted unavailable outcomes, and malformed/non-Findable/mismatched records fail closed.

### Explicit rejections/deferments

- **Codeforces API:** deferred/non-executable after PR #209 because current primary terms do not provide a defensible commercial SaaS reuse basis for the profile metadata. Historical retained evidence remains readable; reactivation requires materially clearer Codeforces-authored terms.
- **ORCID Public API:** rejected for the product baseline because the current Public API terms prohibit use in connection with a revenue-generating product or service. A free endpoint with incompatible commercial terms is not a PersonaLattice source.
- **Hacker News public user API:** rejected under current Y Combinator commercial-use terms. Its technical API fit does not override the product/legal boundary.
- **Stack Exchange generic user search:** rejected as a generic username source because `inname` is substring matching, not identity-quality exact matching. The exact Stack Overflow profile-URL path above is a separate, deterministic applicability rule.
- **Bitbucket Cloud exact repository:** deferred because current Atlassian primary documentation did not clearly establish anonymous access to the exact public-repository operation; a general anonymous quota does not prove endpoint permission. No credential workaround is approved.
- **VIAF:** deferred. ODC-BY/canonical URI terms are workable, but current primary documentation did not establish both a narrow exact-record representation and an operational rate/backoff contract suitable for this baseline.
- **LCNAF/id.loc.gov:** deferred. Current primary documentation did not establish both a defensible commercial-reuse position for cooperatively maintained LCNAF/NACO records and an id.loc.gov-specific rate/backoff contract.
- **GLEIF exact LEI:** deferred. Free access, CC0 reuse and exact LEI retrieval are workable, but the 2026-08-21 primary-source review did not establish a current provider-specific request-rate/backoff contract precise enough to encode as a runtime invariant. Third-party quota claims are not sufficient.
- **SEC EDGAR exact CIK submissions:** deferred under the current provider boundary. The credentialless exact endpoint and SEC fair-access policy are clear, but submissions responses can include large recent-filing histories and do not reliably fit PersonaLattice's 32 KiB raw-response/data-minimization ceiling. Do not weaken the ceiling, fetch filing history merely to discard it, or substitute undocumented partial/search/bulk workarounds.
- **Gravatar:** remains blocked until provider privacy-policy/terms requirements and the free server-side-key boundary are satisfied.
- **WebFinger:** remains blocked until a specific host passes the existing host-policy review.

## M10 evaluation

**Infrastructure complete; representative evidence remains the bottleneck.**

PersonaLattice has separate synthetic, consented and independently reviewed label provenance. The private consented/reviewed runners share one bounded materializer but fix their provenance basis in code; input JSON cannot upgrade its own evidence status. Outputs are aggregate accounting and digests, not raw private identifiers.

Current synthetic graph evidence still favors production depth 2 / 12 over the depth-3 diagnostic candidate: the deeper candidate adds wrong labelled pivots without additional relevant pivots. This is regression evidence, not a population-performance claim.

The next meaningful M10 step is a genuine lawful consented or independently reviewed cohort. Do not manufacture one from repository fixtures or rename synthetic evidence.

## Next gate

1. Continue reviewed source expansion one source at a time, preferring exact applicability and strong provenance over provider count.
2. Run real consented or independently reviewed M10 evidence when it exists and use those results to decide whether source coverage, graph limits or triage policy need changes.
3. Fix newly discovered correctness/security/operator defects when they are concrete; do not reopen frozen architecture without evidence.
4. Keep `docs/CONTINUITY.md`, source-admission notes and operator docs truthful in the same PR as behavior changes.

Success means an operator can answer: what source produced a clue, which retained field caused a pivot, why it was admitted, what evidence affected triage, why expected evidence may be absent, and what remains unknown.

### Bluesky exact profile URL reachability (2026-08-21)

The active Bluesky source accepts exact canonical `bsky.app/profile/<handle>` URLs in addition to handle seeds. URL and handle research share one 30/minute governed runtime budget and the same minimal retained profile contract. DID/post URLs remain out of scope.
