# Source admission queue

This file records current external-source preflight decisions. It is not an allowlist by itself. Re-check primary provider documentation immediately before activation because terms, quotas and authentication rules can change.

## Admission rules

A required source must keep the PersonaLattice baseline at ₹0. A free trial that requires a card, a metered service that can bill automatically, paid hosting/database/proxy infrastructure or paid enrichment does not qualify.

A source also needs a precise applicability rule. Free but fuzzy search is not useful if it creates ambiguous account candidates or wrong recursive pivots.

One external source is activated per PR. Activation uses the existing catalog → binding → DEVELOPMENT provider descriptor → process-wide `ProviderRuntime` → typed source-run → canonical evidence path.

## Approved for implementation review

### Internet Archive Wayback availability

**Decision:** proceed to a bounded adapter PR; not active yet.

**Scope:** exact URL availability metadata only.

Primary documentation reviewed on 2026-08-20:

- Internet Archive Developer Portal, “See whether a website exists in the archives”.
- Internet Archive Developer Portal, “Bots, LLMs, and Automated Access”.
- Internet Archive Developer Portal, “Tools and APIs”.

The documented availability endpoint accepts a URL and returns the nearest available archived snapshot metadata. The current automated-access guidance requires a descriptive User-Agent and requires clients to respect `429 Too Many Requests` and `Retry-After`.

PersonaLattice implementation boundary:

- accept canonical `URL` leads only;
- query the official `https://archive.org/wayback/available` endpoint;
- retain only queried URL, capture availability, capture status, capture timestamp and a validated Wayback snapshot locator;
- do not download archived page content;
- emit no new leads;
- do not infer that archived content belongs to a person;
- validate the returned snapshot locator as HTTP(S), credential-free and hosted by `web.archive.org`;
- cap response size and timeout through the existing provider/runtime boundary;
- map no-capture to a completed zero-observation source result;
- map `429` to the typed remote-rate-limit path and preserve `Retry-After` where valid;
- map malformed provider output to post-attempt result validation, not a pre-attempt policy failure;
- use a descriptive PersonaLattice User-Agent on every automated request.

Why this candidate ranks first: it adds historical context for URLs without introducing fuzzy person search, credentials, subscriber/contact data or new recursive leads.

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