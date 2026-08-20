# Source admission queue

This file records current external-source preflight decisions. It is not an allowlist by itself. Re-check primary provider documentation immediately before activation because terms, quotas and authentication rules can change.

## Admission rules

A required source must keep the PersonaLattice baseline at ₹0. A free trial that requires a card, a metered service that can bill automatically, paid hosting/database/proxy infrastructure or paid enrichment does not qualify.

A source also needs a precise applicability rule. Free but fuzzy search is not useful if it creates ambiguous account candidates or wrong recursive pivots.

One external source is activated per PR. Activation uses the existing catalog → binding → DEVELOPMENT provider descriptor → process-wide `ProviderRuntime` → typed source-run → canonical evidence path.

## Active after current code is merged

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

The provider calls official `wbgetentities` with the exact QID and requests only English labels/descriptions. Retained evidence is limited to QID, bounded English label/description when present, `data_license=CC0`, Wikidata attribution and `identity_claim=false`. Claims, aliases, sitelinks, external identifiers, dates, places, occupations, organizations, contact data and linked entities are not admitted. No Wikidata field becomes a recursive lead.

The source is credentialless and zero-direct-cost. Requests use a meaningful PersonaLattice User-Agent with the repository URL, run serially through a one-concurrency provider budget, stay well below Wikimedia's current User-Agent-only allowance and preserve `429`/`Retry-After`. Provider errors after contact remain attempted outcomes; malformed or mismatched entity results fail closed.

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
