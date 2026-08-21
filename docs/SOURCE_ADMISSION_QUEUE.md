# Source admission queue

This file records current external-source preflight decisions. It is not an allowlist by itself. Re-check primary provider documentation immediately before activation because terms, quotas and authentication rules can change.

## Admission rules

A required source must keep the PersonaLattice baseline at ₹0. A free trial that requires a card, a metered service that can bill automatically, paid hosting/database/proxy infrastructure or paid enrichment does not qualify.

A source also needs a precise applicability rule. Free but fuzzy search is not useful if it creates ambiguous account candidates or wrong recursive pivots.

One external source is activated per PR. Activation uses the existing catalog → binding → DEVELOPMENT provider descriptor → process-wide `ProviderRuntime` → typed source-run → canonical evidence path.

## Active after current code is merged

### Keybase public account basics

**Decision:** admit only for an already-canonical Keybase username and only the public `basics` object.

Primary Keybase documentation re-checked on 2026-08-21:

- Keybase username/public-directory documentation;
- Keybase user lookup API documentation;
- Keybase user-object documentation;
- current Keybase Terms of Service;
- current Keybase Acceptable Use Policy.

Keybase documents usernames as public and immutable, with a 2-16-character namespace made from lowercase letters, numbers and underscores and an alphanumeric first character. PersonaLattice does not coerce a generic username into that namespace; noncanonical values are not applicable and cause no Keybase provider attempt.

The credentialless official lookup is called with `fields=basics`. Retained evidence is restricted to exact username, public UID, account creation timestamp, `account_candidate=true`, `identity_claim=false` and the canonical public profile locator. Profile/full-name data, proofs, external identities, public keys, cryptocurrency addresses and contact-like fields are not requested or admitted. The source emits no recursive leads.

Current terms contemplate use on behalf of an organization/business, while the acceptable-use policy prohibits gathering private information without permission. That combination does not justify broad account enrichment: the source stays inside the explicitly public basics object. The API documentation also warns that the API is evolving, so PersonaLattice validates response shape, exact returned username and UID consistency and fails closed on drift.

No provider quota is relied on. PersonaLattice imposes one attempt, a 4-second timeout, 16 KiB response ceiling, one concurrent request and a 20-request/minute local budget. HTTP `429` preserves `Retry-After`; transient network/5xx states and malformed provider results remain typed attempted outcomes.

### Internet Archive Wayback availability

**Decision:** admitted for exact URL capture-availability metadata.

Primary documentation re-checked on 2026-08-20:

- Internet Archive Developer Portal, “See whether a website exists in the archives”.
- Internet Archive Developer Portal, “Bots, LLMs, and Automated Access”.
- Internet Archive Developer Portal, “Tools and APIs”.

The official availability endpoint returns nearest-capture metadata for a supplied URL. Internet Archive's automated-access guidance requires a descriptive User-Agent and requires clients to respect `429 Too Many Requests` and `Retry-After`.

PersonaLattice keeps the integration deliberately narrow:

- canonical `URL` leads only;
- official `https://archive.org/wayback/available` endpoint;
- retain queried URL, capture availability/status/timestamp and a validated `web.archive.org` snapshot locator;
- never download archived page content through this source;
- emit no new leads and make no person-attribution claim;
- reject malformed snapshot locators, including credentials-bearing or non-Wayback URLs;
- cap timeout/response size and use the shared ProviderRuntime budget;
- zero captures are valid completed no-match outcomes;
- provider `429` is typed as remote rate limiting and valid `Retry-After` is preserved;
- malformed provider output is a post-attempt result-validation failure;
- automated requests carry a descriptive PersonaLattice User-Agent.

This source adds historical URL context without fuzzy person search, credentials, subscriber/contact data or recursive identity claims.

### Stack Overflow exact public profile

**Decision:** admitted only for an exact Stack Overflow profile URL carrying a numeric user ID.

Primary documentation re-checked on 2026-08-20:

- Stack Exchange API Terms of Use;
- Stack Exchange API `/users/{ids}` documentation;
- Stack Exchange API throttling documentation.

The source parses `stackoverflow.com/users/<positive-id>` locally and then calls the official API v2.3 exact-user endpoint with `site=stackoverflow`. It never uses `inname`, display-name search or another fuzzy person lookup.

PersonaLattice retains only bounded account-verification context: numeric Stack Overflow user ID, public display name, reputation, creation timestamp, `identity_claim=false`, explicit Stack Overflow attribution and the canonical returned profile locator. It does not retain `about`, posts/comments, location, website, profile image, email or other contact fields. It emits no leads.

The source uses anonymous reads only, stays inside a conservative local budget, honors provider `429`/`Retry-After` and API `backoff`, and keeps Stack Overflow attribution visible with the canonical source locator. The account is evidence about the supplied profile URL, not proof of subject identity.

### OpenAlex exact author

**Decision:** admitted only for an exact OpenAlex author URL when the free server-side API key is configured.

Primary OpenAlex documentation re-checked on 2026-08-21:

- single-author retrieval (`GET /authors/{id}`);
- API authentication and pricing;
- API changelog for the 2026 API-key requirement;
- OpenAlex ID guidance and author-name ambiguity;
- CC0 data/reuse documentation.

PersonaLattice accepts only canonical `https://openalex.org/A<positive-digits>` author URLs. It does not search by author name, ORCID, institution, work, topic or other person-like text. The URL already identifies the scholarly entity before provider execution.

The provider calls only the singleton author endpoint and requests four fields: canonical ID, display name, works count and cited-by count. Retained evidence adds `data_license=CC0`, OpenAlex attribution and `identity_claim=false`. ORCID/Scopus/MAG IDs, affiliations, locations, topics, alternative names, work lists, abstracts/full text and contact details are not retained. No OpenAlex field becomes a recursive lead.

OpenAlex currently requires a free API key. PersonaLattice keeps it server-side in `OPENALEX_API_KEY` and sends it as bearer authorization rather than putting it in the URL. A missing key is a pre-attempt `credential_not_configured` state. Provider `429`, transient failures and malformed responses retain their existing attempted-failure semantics.

If OpenAlex responds with a different author ID than the exact ID supplied by the operator, the adapter fails closed rather than silently substituting another profile. This includes merged-ID behavior: identity reconciliation must remain explicit, not hidden inside a source adapter.

### Wikidata exact entity

**Decision:** admitted only for an exact Wikidata item URL carrying a `Q<positive-digits>` entity ID.

Primary Wikimedia/Wikidata documentation re-checked on 2026-08-21:

- Wikidata licensing and copyright policy for structured data;
- Wikibase Action API `wbgetentities` documentation;
- Wikimedia Foundation API Usage Guidelines and User-Agent policy;
- Wikimedia's 2026 API rate-limit documentation.

PersonaLattice accepts only canonical `https://www.wikidata.org/wiki/Q<positive-digits>` item URLs. It does not search by person name, alias, property, statement, sitelink or external identifier. The operator-supplied URL identifies the knowledge-graph entity before provider execution.

The provider calls official `wbgetentities` with the exact QID and requests only English labels/descriptions. Retained evidence is limited to QID, bounded English label/description when present, `data_license=CC0`, Wikidata attribution and `identity_claim=false`. It does not request or retain structured claims, aliases, sitelinks, external identifiers or linked entities. The optional English description is retained verbatim as bounded public descriptive text; it can contain ordinary biographical wording, but PersonaLattice does not parse that prose into dates, locations, occupations, organizations, identity claims or recursive leads.

The source is credentialless and zero-direct-cost. Requests use a meaningful PersonaLattice User-Agent with the repository URL, run serially through a one-concurrency provider budget, stay well below Wikimedia's current identified-client allowance, send `maxlag=5`, and preserve `429`/`Retry-After`. MediaWiki API-level `ratelimited` and `maxlag` errors are also mapped to typed rate/backoff outcomes. Provider errors after contact remain attempted outcomes; malformed or mismatched entity results fail closed.

### ROR exact organization

**Decision:** admitted only for an exact canonical `https://ror.org/<id>` organization URL.

Primary ROR documentation re-checked on 2026-08-21:

- ROR Terms of Use and CC0 registry-data policy;
- ROR identifier-format guidance;
- REST API v2 singleton organization retrieval;
- v2.1 schema guidance for `ror_display`, status and organization types;
- current Client ID and rate-limit guidance.

ROR identifiers and registry metadata are published under CC0 and are available without access/use restrictions. PersonaLattice uses only `GET /v2/organizations/{id}` after locally validating the exact canonical ROR URL. It never uses organization search, affiliation matching, autocomplete, reverse lookup or bulk enumeration.

Retained evidence is restricted to the canonical ROR ID, exactly one bounded `ror_display` name, `active` record status, at most eight bounded organization types when present, `data_license=CC0`, ROR attribution, canonical source provenance and `identity_claim=false`. External identifiers, domains, links, aliases beyond the selected display name, relationships, locations/addresses/geocodes, search candidates and contact-like data are ignored. Provider-specific field names are used so the generic lead extractor cannot silently turn the organization name into a recursive clue; the source emits no leads.

The source is credentialless and zero-direct-cost. ROR has announced a lower unidentified-client tier of 50 requests per five minutes; PersonaLattice imposes the tighter local budget of eight requests/minute, one concurrency slot, one attempt, a 4-second timeout and a 32 KiB response ceiling. Client ID registration is currently paused, so the required baseline does not depend on it. `404` is a completed no-match; `429` preserves valid `Retry-After`; 408/5xx/network failures remain attempted transient failures; malformed records, non-active records and returned-ID mismatches fail closed.

### Crossref exact work

**Decision:** admit only for an exact `https://doi.org/<doi>` URL supplied by the operator.

Primary Crossref documentation re-checked on 2026-08-21:

- REST API overview and singleton `GET /works/{doi}` endpoint;
- public access/authentication guidance;
- metadata reuse/licensing guidance;
- current REST API rate-limit and backoff guidance.

Crossref's public REST API requires no signup or credential. PersonaLattice uses only the singleton work endpoint after locally parsing an exact DOI resolver URL. It does not use `/works` search, query, filter, cursor or list operations and does not search by title, person name, ORCID, affiliation or other bibliographic text.

Retained evidence is intentionally narrow: canonical DOI, one bounded title, a valid publication year when present, up to eight bounded author display names, Crossref attribution and `identity_claim=false`. Author names remain display-only and emit no recursive leads. Abstracts, ORCID/author identifiers, affiliations, references, funders, subjects, relation/update expansion, license/full-text/resource links and contact data are ignored even when Crossref returns them.

Crossref says almost all deposited bibliographic metadata can be reused for any purpose, while abstracts may remain subject to publisher/author copyright. PersonaLattice therefore excludes abstracts rather than treating the entire response as unrestricted content.

The provider runs with no secret, one attempt, a 4-second timeout, 32 KiB adapter response ceiling, one concurrent request and a local 30-request/minute budget. That local budget stays materially below Crossref's current anonymous public single-record allowance. `404` is a completed no-match; `429` preserves `Retry-After`; 408/5xx/network failures remain attempted transient failures; malformed data and returned-DOI mismatch fail closed. DOI comparison is case-insensitive, but the adapter never substitutes a different identifier.

### DataCite exact DOI fallback

**Decision:** admit only as a fallback after the exact Crossref source completes normally with zero observations.

Primary DataCite documentation re-checked on 2026-08-21:

- DataCite REST API overview and public API authentication guidance;
- singleton `GET /dois/{id}` retrieval;
- current REST API rate limits;
- DataCite Data File Use Policy and CC0 metadata guidance.

DataCite's public singleton API is credentialless. Current unidentified clients are documented at 500 requests per five minutes per IP; PersonaLattice uses one concurrency slot and a local 30-request/minute budget instead. Provider `429` preserves valid `Retry-After`; 408/5xx/network failures remain attempted transient failures; malformed singleton envelopes, non-Findable records and DOI mismatches fail closed.

The critical ordering rule is source truth, not hit rate. PersonaLattice attempts Crossref first. If Crossref returns an exact observation, DataCite is not attempted. If Crossref completes with zero observations, DataCite may run. If Crossref was rate-limited, unavailable, malformed or otherwise failed after an attempt, DataCite does not run and cannot hide the Crossref failure.

Retained DataCite evidence is limited to the canonical DOI, one bounded title, valid publication year/resource type when present, up to eight bounded creator display names, `data_license=CC0`, DataCite attribution and `identity_claim=false`. Creator names remain display-only. Name identifiers/ORCID, affiliations, descriptions, geolocations, funding, related identifiers, subjects, rights/full-text/resource URLs, usage/activity fields and contact/account data are excluded. The source performs no search/list/relation expansion and emits no recursive leads.

DataCite releases deposited metadata under CC0 for reuse, while explicitly noting that privacy/publicity and other rights of represented individuals can still apply. PersonaLattice therefore keeps the retained field set narrow instead of treating CC0 as permission for unrestricted personal-data expansion.

## Rejected for the baseline

### ORCID Public API

**Decision:** reject for PersonaLattice's product baseline under the current Public API terms.

The public API is free for non-commercial use, but the current terms prohibit use of the public APIs in connection with a revenue-generating product or service. PersonaLattice is being built as a real product, so treating that API as a permanent free SaaS dependency would create avoidable commercial/legal debt.

Revisit only if ORCID terms or the product's usage model materially change. Do not substitute scraping for the rejected API path.

### Hacker News public user API

**Decision:** reject under the current Y Combinator terms for PersonaLattice's intended commercial path.

The API is technically attractive: exact case-sensitive user IDs, credentialless public reads and no documented API rate limit. A deeper terms review found broad current commercial-use restrictions covering site use/access and account/karma/content material. The API announcement does not provide a clear commercial-use grant that is safe to treat as overriding those terms.

Do not activate Hacker News account metadata merely because the endpoint is free. Revisit only if current primary terms change or written permission makes the commercial-use boundary clear enough.

## Deferred

### Stack Exchange user search

**Decision:** do not activate as generic username research.

The official `/users` API supports `inname`, but that parameter is substring search over display names. It is not an exact global username lookup. Turning those results into account evidence or recursive pivots would increase false candidates.

This does not apply to the admitted exact Stack Overflow profile-URL source above. That path derives a numeric user ID from an already-supplied profile URL and never performs fuzzy search.

### Gravatar

Keep planned. Current admission remains blocked by provider privacy-policy/terms requirements and the server-side credential boundary. It must not become necessary to the zero-spend baseline.

### WebFinger

Keep planned. The transport/admission machinery exists, but production host approval stays empty until a specific host passes current terms/privacy review. Do not turn generic WebFinger discovery into unrestricted ActivityPub actor fetching.

## Discovery-only indexes

Repositories such as `public-apis/public-apis` and machine-readable directories such as APIs.guru are useful for finding candidates. They do not establish provider permission, privacy suitability, commercial-use rights, quota stability or true zero cost. Every activation decision must be grounded in the provider's own current documentation.
