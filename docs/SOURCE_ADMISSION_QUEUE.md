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

## Rejected for the baseline

### ORCID Public API

**Decision:** reject for PersonaLattice's product baseline under the current Public API terms.

The public API is free for non-commercial use, but the current terms prohibit use of the public APIs in connection with a revenue-generating product or service. PersonaLattice is being built as a real product, so treating that API as a permanent free SaaS dependency would create avoidable commercial/legal debt.

Revisit only if ORCID terms or the product's usage model materially change. Do not substitute scraping for the rejected API path.

## Deferred

### Stack Exchange user search

**Decision:** do not activate as generic username research.

The official `/users` API supports `inname`, but that parameter is substring search over display names. It is not an exact global username lookup. Turning those results into account evidence or recursive pivots would increase false candidates.

A future explicit Stack Exchange account URL or numeric user-ID source could be reconsidered because that would have a precise applicability rule. If used, honor Stack Exchange's documented request quota, per-IP throttling and `backoff` field.

### Gravatar

Keep planned. Current admission remains blocked by provider privacy-policy/terms requirements and the server-side credential boundary. It must not become necessary to the zero-spend baseline.

### WebFinger

Keep planned. The transport/admission machinery exists, but production host approval stays empty until a specific host passes current terms/privacy review. Do not turn generic WebFinger discovery into unrestricted ActivityPub actor fetching.

## Discovery-only indexes

Repositories such as `public-apis/public-apis` and machine-readable directories such as APIs.guru are useful for finding candidates. They do not establish provider permission, privacy suitability, commercial-use rights, quota stability or true zero cost. Every activation decision must be grounded in the provider's own current documentation.