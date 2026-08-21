# Continuity

This file is the handover for the next PersonaLattice engineering session. Read it before proposing work.

## Authoritative repository state

Repository: `tushar-rawat-22/persona-lattice`

Authoritative branch: `main`

Engineering-freeze baseline: PR #168, merged as `5d774a9fadc336d43e06491183d9035d016db04f` after exact-head CI passed.

Keybase source activation: PR #177 merged as `611ef00cd14858f5e60e2d32add3ec4cee47b025` after exact head `ad28424449a5719e8a3e8d66e802f60515d2c318` passed CI run `32425561458` across Python 3.11/3.13, web and the production API image.

Crossref exact-work activation: PR #180 merged as `0d049af3af7f7450d348477bfb2775921cc25b3b`. It provides exact DOI URL admission, credentialless singleton transport, governed catalog/binding/runtime ownership, typed source-run reporting, bounded canonical evidence and source-policy regressions.

DataCite exact-DOI fallback activation: PR #182 merged as `e4cb6318bed78f8a72ea15b41db5f55a12a45f9d` after exact head `a7772d0f4bdfaebfb243a66b115f3b4aeeac3b10` passed CI run `32435388198` across Python 3.11/3.13, web and the production API image. DataCite is intentionally subordinate to Crossref: it runs only after Crossref completes normally with zero observations. Crossref attempted failures never fall through to DataCite.

ROR exact-organization activation: PR #185 merged as `1f5b1a897ab08763788f6024d727cea27a299be3` after exact head `b2c67addb269f42571422d19710791284884e644` passed CI run `32437343476`. Only an exact canonical `https://ror.org/<id>` URL is applicable; the source uses the credentialless v2 singleton organization endpoint, retains a narrow CC0 registry record, emits no leads and does not use organization search or affiliation matching.

DBLP exact-person activation: PR #187 merged as `905f9fc8915487a002e54a81e3d23b443ea19072` after exact head `4e5de2580ea8cb2881f1520e5790b15362ea80c6` passed CI run `32440833347`. It is limited to explicit canonical `https://dblp.org/pid/<pid>` URLs and one minimal public-SPARQL query for the exact `dblp:Person` resource plus `dblp:primaryCreatorName`; it emits no leads and does not retrieve bibliography or coauthor context.

Companies House exact-company activation: PR #191 merged as `079e3dc3c79f2a26fd71e869b671db30e5edb451` after exact head `820470b173050d75c9bcd98ae974399e58ce33db` passed CI run `32451537243`. The package admits only explicit canonical public company URLs, uses the exact company-profile endpoint with a free server-side API key, keeps the credential out of URLs/evidence, retains a narrow non-person company record, emits no leads and excludes officer/PSC/address/filing/search expansion.

The next GitHub source extension is deliberately not a second provider. Exact public repository URLs are routed through the existing `github_public_api` descriptor, process-owned adapter and 50-request/hour local budget. Repository observations retain only bounded public repository identity/state metadata and emit no leads; owner login is display-only because repository owners can be organizations.

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
- GitHub public profile API plus exact public repository metadata through one shared provider budget;
- GitLab public profile API;
- Codeforces `user.info`;
- Bluesky public AppView profile lookup for valid AT handles;
- Keybase public account basics for canonical Keybase usernames;
- public DNS infrastructure metadata;
- Internet Archive Wayback capture-availability metadata for canonical URLs;
- Stack Overflow exact public-profile metadata for explicit numeric profile URLs;
- OpenAlex exact-author metadata when a free server-side key is configured;
- Wikidata exact-item CC0 metadata for explicit item URLs;
- ROR exact-organization CC0 metadata for explicit canonical ROR URLs;
- Companies House exact-company public-register metadata for explicit canonical company URLs when a free server-side key is configured;
- DBLP exact-person CC0 metadata for explicit canonical person PID URLs;
- Crossref exact-work bibliographic metadata for explicit DOI resolver URLs;
- DataCite exact-DOI CC0 fallback metadata after a clean Crossref no-match;
- authoritative RDAP for explicit DOMAIN seeds.

Optional:

- Brave exact public-web search when configured. It is metered and must never become a required dependency.

GitHub username and repository lookups share one `github_public_api` runtime owner and one 50-request/hour local budget. Exact repository applicability requires a canonical `https://github.com/<owner>/<repo>` URL with no credentials, custom port, query, fragment or extra route. The repository path uses only official `GET /repos/{owner}/{repo}` and retains repository full name, owner login/type, explicit public-state verification and optional fork/archived booleans plus canonical provenance. Description/content, popularity counters, contributors, commits, issues, releases and contact-like fields are excluded. `github_repository_owner_login` is display-only and repository observations emit no leads.

Keybase is exact-username account metadata only. Applicability requires an already-canonical Keybase username: 2-16 lowercase alphanumeric/underscore characters with an alphanumeric first character. The source requests only the official API `basics` object and retains exact username, public UID, account creation timestamp, `account_candidate=true`, `identity_claim=false` and canonical `https://keybase.io/<username>` provenance. Profile text/full name, proofs, linked external identities, public keys, cryptocurrency addresses and contact-like data are not requested or admitted. It emits no leads. Noncanonical usernames skip Keybase before provider execution.

Wayback is intentionally metadata-only. It queries the official availability endpoint, sends a descriptive PersonaLattice User-Agent, validates the returned `web.archive.org` snapshot locator, and retains only queried URL plus capture availability/status/timestamp. It does not fetch archived page content, emit leads or make a person-attribution claim. Provider rate limits and malformed outputs stay visible through typed source-run reporting.

Stack Overflow is exact-URL account metadata only. Applicability requires a supplied `stackoverflow.com/users/<positive-id>` profile URL; the provider then calls the official exact-user API. It retains only prefixed user ID/display name/reputation/creation metadata, API attribution, `identity_claim=false`, and the canonical returned profile locator. It does not retain profile prose, posts/comments, location, website, image or contact fields, and it emits no leads. Generic Stack Exchange `inname` user search remains outside the product.

OpenAlex is exact-author-URL metadata only. Applicability requires `https://openalex.org/A<positive-digits>` with no credentials, port, query or fragment. The provider calls only the official singleton author endpoint and retains author ID, display name, works count, cited-by count, CC0 attribution and `identity_claim=false`. It does not retain ORCID/Scopus/MAG identifiers, affiliations, locations, topics, alternative names, publications, full text or contact fields and emits no leads. The free key stays server-side in `OPENALEX_API_KEY` and is sent as bearer authorization, never in a URL. Missing key is `credential_not_configured` with no provider attempt. A returned author ID mismatch fails closed rather than silently switching scholarly identities.

Wikidata is exact-item-URL metadata only. Applicability requires `https://www.wikidata.org/wiki/Q<positive-digits>` with no credentials, port, query or fragment. The provider calls official `wbgetentities` for that QID and requests English labels/descriptions only. It retains the QID, bounded English label/description when present, CC0 attribution and `identity_claim=false`; it does not request or retain structured claims, aliases, sitelinks, external identifiers or linked entities, and emits no leads. The bounded description is public descriptive text and is never parsed into identity claims or recursive leads. Requests are credentialless, use an identifying User-Agent, one-concurrency/30-per-minute local budget, `maxlag=5`, and typed HTTP/API-level rate/backoff handling.

ROR is exact-organization-URL metadata only. Applicability requires the canonical `https://ror.org/<id>` form with no credentials, custom port, query, fragment or trailing path. The provider performs one official credentialless `/v2/organizations/{id}` singleton read and retains only the canonical ROR ID, exactly one bounded `ror_display` name, `active` record status, at most eight bounded organization types, CC0 attribution and `identity_claim=false`. It excludes external IDs, domains, links, aliases beyond the selected display name, relationships, locations/addresses/geocodes, search candidates and contact-like fields. The retained display name uses a provider-specific field key so generic extraction does not silently turn it into an organization lead; provider and extraction regressions require zero emitted leads. PersonaLattice applies one attempt, a 4-second timeout, 32 KiB response ceiling, one concurrency slot and an eight-request/minute local budget. `404` is a completed no-match, `429` preserves `Retry-After`, transient failures stay attempted-unavailable, and malformed/non-active/mismatched records fail closed.

Companies House is exact-company-URL metadata only. Applicability requires `https://find-and-update.company-information.service.gov.uk/company/<company-number>` with no credentials, custom port, query, fragment or trailing path. The provider calls only the official exact company-profile endpoint and sends `COMPANIES_HOUSE_API_KEY` as the HTTP Basic username with a blank password. The key never appears in request URLs, retained evidence or client configuration. Missing key is a pre-attempt `credential_not_configured` state.

The retained company record is limited to company number, bounded registered name/status/type, optional valid incorporation date, Companies House public-register attribution and `identity_claim=false`. Registered-office addresses, officers/directors/secretaries/PSCs, person names, SIC/business descriptions, accounts/confirmation fields, insolvency/charges, filing history/document links, previous names, jurisdiction/location expansion and contact-like fields are excluded. Provider-specific names keep the registered name out of generic lead extraction; regression coverage requires zero emitted leads. PersonaLattice uses one attempt, a 4-second timeout, 32 KiB response ceiling, one concurrency slot and 30 requests/minute, well below the documented 600 requests/five-minute provider limit.

DBLP is exact-person-PID metadata only. Applicability requires a canonical `https://dblp.org/pid/<pid>` URL with no credentials, custom port, query, fragment, suffix or trailing path. PIDs remain case-sensitive. The provider sends one exact-resource query to `https://sparql.dblp.org/sparql`, constrains the resource to `dblp:Person`, and asks only for `dblp:primaryCreatorName`. It retains the canonical PID URL, one bounded primary name, CC0 attribution and `identity_claim=false`. Publication lists/counts, coauthors, affiliations, ORCID/external IDs, homepages, alternate names and contact-like data are not requested or admitted. `dblp_primary_name` is a provider-specific display field and extraction regressions require zero emitted leads. The shared public SPARQL service is treated as beta infrastructure: one attempt, 4-second timeout, 32 KiB response ceiling, one concurrency slot and six requests/minute locally. Empty results are no-match; `429` preserves `Retry-After`; transient failures stay attempted-unavailable; mismatched, duplicate or malformed results fail closed.

Crossref is exact-work metadata only. Applicability requires a canonical `https://doi.org/<doi>` URL with no credentials, custom port, query or fragment. The provider performs one anonymous official `/works/{doi}` singleton read and retains only the DOI, one bounded title, an optional valid publication year, up to eight bounded author display names, explicit Crossref attribution and `identity_claim=false`. Author names are display-only and emit no leads. Abstracts, ORCID/other author identifiers, affiliations, references, funders, subjects and full-text/resource/license expansion are not admitted. The adapter uses one attempt, a 4-second timeout, 32 KiB response ceiling, one-concurrency/30-per-minute local budget, preserves `429`/`Retry-After`, and fails closed on malformed or mismatched DOI results.

DataCite is an exact-DOI fallback, not an independent discovery query. It reuses the canonical DOI URL applicability rule and executes only when Crossref completed normally with no observation. If Crossref was rate-limited, unavailable, malformed or otherwise failed after an attempt, DataCite does not execute and the Crossref failure remains visible. The provider calls credentialless public `/dois/{id}` singleton retrieval and retains only DOI, bounded title, optional valid publication year/resource type, up to eight bounded creator display names, `data_license=CC0`, explicit DataCite attribution and `identity_claim=false`. It excludes creator identifiers/ORCID, affiliations, descriptions, geolocations, funding, related identifiers, subjects, rights/resource URLs and usage/activity fields, and emits no leads. Current DataCite metadata policy is CC0 but does not remove privacy/publicity rights in represented individuals.

Planned/review-gated entries in the source catalog are not executable merely because code or a catalog record exists.

## M10 status

The repository-side M10 ingestion/evaluation path is ready. The blocker is real evidence.

Use `docs/M10_CONSENTED_COHORT_RUNBOOK.md` only when genuine consent records support the labels. Use `docs/M10_REVIEWED_COHORT_RUNBOOK.md` only when a real independent review record supports the labels. Do not convert repository fixtures, input flags or identifier hashes into either evidence basis.

Production depth 2 / 12 currently beats the depth-3 diagnostic candidate on the synthetic cohort: the deeper candidate adds attempts and wrong labelled pivots without additional relevant pivots. This is regression evidence only.

Do not publish false-positive/false-negative, probability, calibration or population-performance claims until cohort design and denominators support those terms.

## Source expansion state

Source expansion is the main engineering stream alongside real M10 evaluation. `docs/SOURCE_ADMISSION_QUEUE.md` records current preflight decisions; source-specific admission records may provide narrower implementation contracts.

GitHub exact repository metadata extends the existing source rather than adding a provider. Current primary GitHub documentation was re-checked on 2026-08-21: public repository retrieval is available without authentication, the unauthenticated REST limit is 60 requests/hour per originating IP, and current API terms prohibit abusive limit-circumvention/spam use. PersonaLattice keeps the existing 50/hour shared GitHub budget across username profiles and repositories and adds no new quota pool. Exact repository context is non-recursive and data-minimized; see `docs/source-admissions/GITHUB_EXACT_REPOSITORY.md`.

Wayback was the first post-freeze source admission. Its contract is exact-URL historical availability metadata only. Treat zero capture as a valid no-match, `429` as a remote rate limit, malformed provider output as a post-attempt validation failure, and transient provider/network failure as unavailable. The source emits no recursive candidates.

Stack Overflow is the second admitted post-freeze source. Its applicability boundary is an exact profile URL with a numeric user ID, not a username/display-name query. Anonymous requests use the official Stack Exchange API, stay under a conservative local budget, preserve provider `Retry-After`/API `backoff`, and keep Stack Overflow attribution visible with canonical provenance.

OpenAlex is an admitted post-freeze source. Its applicability is an exact author entity URL, not a person-name search. Current primary documentation was re-checked on 2026-08-21: API keys are required and free, bearer authentication is supported, singleton-by-ID retrieval is a free operation, author names are not safe identifiers, and the data is CC0. Re-check those provider facts before future source-policy changes.

Wikidata is an admitted source in `main`. Its applicability is an exact item URL, not a person/entity-name search. Current primary documentation was re-checked on 2026-08-21: structured data is CC0; `wbgetentities` supports exact QID retrieval; automated clients must identify themselves and respect rate/backoff policy. PersonaLattice stays far below the current identified-client allowance and requests no claims or linked-entity expansion.

Keybase is admitted via PR #177. Primary documentation was re-checked on 2026-08-21: usernames are public/immutable and restricted to the canonical 2-16-character lowercase namespace; the public lookup API supports requesting only `basics`; current terms contemplate organizational/business use, while the acceptable-use policy forbids collecting private information without permission. The implementation therefore keeps only public basics, sends no credentials, emits no leads and deliberately excludes profiles, proofs, keys and external-identity expansion. The API is documented as evolving, so shape/username/UID validation fails closed. Exact head `ad28424449a5719e8a3e8d66e802f60515d2c318` passed CI run `32425561458` before the expected-head squash merge.

Crossref is active on `main` via PR #180. Primary documentation was re-checked on 2026-08-21: public API access requires no signup, exact work retrieval is `GET /works/{doi}`, almost all deposited bibliographic metadata is reusable for any purpose, abstracts can remain copyrighted, and anonymous public clients must respect current public limits/backoff. PersonaLattice excludes abstracts and uses only exact DOI singleton reads under a much tighter local budget. No Crossref search/list operation or author-name pivot is authorized.

DataCite is active on `main` via PR #182. Primary DataCite documentation was re-checked on 2026-08-21: public singleton DOI retrieval requires no authentication, public API records are Findable DOI metadata, the unidentified public tier is currently 500 requests per five minutes per IP, and deposited metadata is released under CC0 subject to third-party privacy/publicity rights. PersonaLattice is tighter: 30 requests/minute locally, one attempt, one concurrency slot, 4-second timeout, 32 KiB adapter ceiling, no search/list/relation expansion, and fallback execution only after a clean Crossref no-match.

ROR is active on `main` via PR #185. Primary ROR documentation was re-checked on 2026-08-21: ROR IDs/registry metadata are CC0 and unrestricted; exact v2 organization retrieval is supported by ID; the current schema exposes one `ror_display` name, record status and organization types; and ROR has announced a lower unidentified-client tier of 50 requests per five minutes. PersonaLattice stays below that announced tier with eight requests/minute locally and does not depend on Client ID registration, which is currently paused. Exact head `b2c67addb269f42571422d19710791284884e644` passed CI run `32437343476` before merge.

DBLP is active on `main` via PR #187. Primary DBLP documentation was re-checked on 2026-08-21: all DBLP metadata is CC0 and can be reused commercially; persistent PIDs are the stable person identifiers; `dblp:primaryCreatorName` is the primary creator-name property; and the public SPARQL service is a shared beta endpoint with rate limiting against aggressive scripting. PersonaLattice deliberately avoids the full person-bibliography export because that would retrieve much more publication/coauthor context than an exact PID check needs. Exact head `4e5de2580ea8cb2881f1520e5790b15362ea80c6` passed CI run `32440833347` before PR #187 merged as `905f9fc8915487a002e54a81e3d23b443ea19072`.

Companies House is active on `main` via PR #191. Primary documentation was re-checked on 2026-08-21: the exact company-profile endpoint is a read-only public-data path; API-key Basic authentication is documented; public API access is free; the default limit is 600 requests per five minutes; and third-party users remain responsible for data-protection/copyright compliance when reusing public-register information. PersonaLattice intentionally retains no registered-office address, officer/PSC/person data, filings or search results and stays at 30 requests/minute locally. Exact head `820470b173050d75c9bcd98ae974399e58ce33db` passed CI run `32451537243` before PR #191 merged as `079e3dc3c79f2a26fd71e869b671db30e5edb451`.

VIAF exact authority metadata was re-reviewed on 2026-08-21 and remains deferred rather than admitted. OCLC still lists VIAF as a production API and VIAF data is ODC-BY with canonical numeric URIs, but the primary materials available to us did not establish a narrow exact-record representation plus practical rate/backoff contract strongly enough to justify a new production dependency. VIAF cluster records are also materially richer than PersonaLattice needs. Do not implement VIAF name search, autosuggest, SRU search or a broad cluster parser as a workaround.

LCNAF/id.loc.gov review Issue #189 was closed `not_planned` on 2026-08-21. Machine-readable exact authority resources exist, but current primary documentation did not establish both a defensible future-commercial reuse position for cooperatively maintained LCNAF/NACO records and an id.loc.gov-specific rate/backoff contract. Do not work around those blockers with search/suggest, broad SKOS parsing or borrowed limits from the separate loc.gov JSON API.

GLEIF exact LEI metadata remains deferred. Current primary materials establish free access, CC0 reuse and exact LEI retrieval, but the 2026-08-21 review did not establish a provider-primary request-rate/backoff contract precise enough to encode as a runtime invariant. Do not substitute third-party quota claims merely to activate the source.

SEC EDGAR exact-CIK submissions review Issue #192 was closed `not_planned`. The exact endpoint is credentialless and SEC's fair-access policy is clear, but the response includes recent filing-history arrays and can exceed PersonaLattice's required 32 KiB raw-response ceiling. Do not weaken the ceiling, fetch large filing history simply to discard it, use undocumented partial/range behavior or swap in fuzzy ticker/name/search/bulk endpoints.

Current explicit rejections/deferments include:

- ORCID Public API is not suitable for a future revenue-generating PersonaLattice baseline under its current public API terms.
- Hacker News public-user metadata is rejected under current Y Combinator commercial-use terms despite a technically attractive free API.
- Stack Exchange `inname` user search is substring-based and therefore too fuzzy to become generic recursive username evidence; this does not affect the exact Stack Overflow profile-URL source.
- VIAF exact authority retrieval is deferred until current primary documentation supports a narrow, stable exact-record representation and operational contract; fuzzy VIAF discovery remains out of scope regardless.
- LCNAF/id.loc.gov is deferred until both cooperatively maintained record reuse and service-specific operating limits are defensible from current primary documentation.
- GLEIF exact LEI lookup is deferred until a current GLEIF-primary request-rate/backoff contract is available.
- SEC EDGAR exact-CIK submissions are deferred while the provider response shape conflicts with the raw-response/data-minimization ceiling.

If provider documentation changes, repeat the preflight instead of trusting this handover.

## Next engineering gate

1. Finish exact GitHub repository URL support through the existing `github_public_api` runtime owner, preserving the single shared 50/hour budget, zero-lead repository contract and username behavior. Merge only after the exact PR head passes the full required CI matrix.
2. After that package, review the next high-value exact ₹0 source from current primary documentation only. Reject sources whose terms, privacy model, operational contract, response shape or matching semantics do not fit the product even if the endpoint is free.
3. Keep exact-source boundaries green for GitHub, Keybase, Wayback, Stack Overflow, OpenAlex, Wikidata, ROR, Companies House, DBLP and Crossref/DataCite; do not expand them into content scraping, fuzzy person/entity/organization search or hidden identity reconciliation.
4. Keep the Crossref→DataCite exact-DOI ordering regression green; never use the fallback to conceal Crossref attempted failures or widen DOI research into fuzzy search.
5. When genuine consented/reviewed M10 evidence exists, run it before changing production graph limits or M5 semantics.
6. Fix concrete correctness/security/operator defects as discovered; do not reopen frozen architecture or create cosmetic PRs to simulate progress.

A new block must improve defensible source coverage, real evaluation, correctness, security or a concrete investigator task.
