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
- GitHub public profiles from exact username seeds or canonical profile URLs plus exact public repository metadata through one shared provider budget;
- GitLab public profiles plus exact subgroup-aware public project metadata through one shared provider budget;
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

Codeforces is no longer executable. PR #209 moved the source to `REVIEW_REQUIRED`, removed its source binding and process runtime ownership, and made central policy report a pre-attempt `provider_policy` block while preserving historical retained evidence. Reactivation requires materially clearer Codeforces-authored commercial SaaS API/data-use terms.

GitHub username, exact profile-URL and repository lookup share the same process-owned `github_public_api` adapter and the same 50-request/hour local budget. Profile URL applicability is only an exact canonical `https://github.com/<login>` URL with one non-empty path segment, no credentials, custom port, query or fragment, and no known reserved GitHub root route. The path reuses official `GET /users/{username}` and still requires case-insensitive exact login agreement, `type=User` and a canonical returned `html_url`; organizations, bots and unsupported account types fail closed after provider contact. Repository applicability is only an exact `https://github.com/<owner>/<repo>` URL. Repository-owner login remains display-only because owners can be organizations; repository observations emit no leads.

GitLab username, exact public-email and exact public-project lookup share the same process-owned `gitlab_public_api` adapter and the same 20-request/minute local budget. Project applicability accepts exact canonical `https://gitlab.com/<namespace...>/<project>` paths with at least two non-empty segments. Local admission rejects credentials, custom ports, query/fragment, `.git`, empty or malformed `.`/`-` segments, organization-scoped `/o/...` routes and GitLab `/-/` action routes. The provider calls only official `GET /api/v4/projects/{URL-encoded full project path}` and requires `visibility=public`, exact full `path_with_namespace`, namespace `full_path` matching every namespace segment before the project name, and an exact canonical returned `web_url`. Retained project fields remain provider-specific display context and emit no leads. Username/public-email requests retain GitLab's documented `humans=true` filter.

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

### GitHub exact public profile URL

**Active through the existing GitHub provider.**

Only an exact canonical `https://github.com/<login>` URL is applicable. Username seeds, profile URLs and repository URLs share one provider descriptor, one adapter instance and the existing 50-request/hour local budget; this path adds no second quota pool. Known GitHub root routes are rejected locally so site navigation cannot be interpreted as a person profile. The provider response remains authoritative for account existence rather than a new local username grammar.

The adapter reuses official `GET /users/{username}` and the reviewed username-profile field set. Exact case-insensitive login agreement, `type=User`, and a canonical returned profile locator are mandatory. Organization, Bot, missing or unsupported account types fail closed after the attempted provider request. No new followers/org/member/repository/event/gist/commit or private-resource lookup is introduced.

The detailed admission record is `docs/source-admissions/GITHUB_EXACT_PROFILE_URL.md`.

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

### Explicit rejections/deferments

- **Codeforces API:** deferred/non-executable pending materially clearer Codeforces-authored commercial SaaS reuse terms. PR #209 moved the source to `REVIEW_REQUIRED`, removed executable binding/runtime ownership and made central policy block execution before provider contact while preserving historical reads.
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