# ADR 0064 — Gravatar activation requires a privacy-policy gate

Status: accepted for pre-activation review

## Context

Gravatar is a plausible zero-spend enrichment source for an already-known email. Its current Profiles API accepts a SHA-256 identifier derived from a trimmed, lower-cased email address. Gravatar documents the Profiles API as free, with higher limits for authenticated requests, and recommends a server-side API key for production use.

The API returns substantially more profile data than PersonaLattice needs. The current profile schema includes location, company, verified accounts, contact information, payment information, biography and image URLs in addition to basic profile identity fields.

Automattic's current API terms also require applications using its APIs to disclose how API data is collected, stored and refreshed and to provide an accessible privacy policy. PersonaLattice does not currently expose a privacy-policy surface. Activating Gravatar before that requirement is satisfied would be a terms-compliance defect, even if the network adapter itself were technically correct.

## Decision

Add a local, network-free Gravatar admission boundary now, but keep `gravatar_public_profile` planned, unbound and non-recursive.

The preflight contract:

- derives only the provider-local SHA-256 identifier required by Gravatar; this does not replace PersonaLattice's canonical email normalization;
- requires the returned profile hash to match the requested email-derived hash;
- accepts only an HTTPS `gravatar.com/<slug>` profile locator as canonical provenance;
- retains only optional display name plus `account_candidate=true`, `identity_claim=false` and public-profile visibility metadata;
- does not admit location, company, verified-account URLs, links, contact information, payment information, biography, avatar images, interests, languages or other upstream fields;
- performs no network request and owns no API key.

## Activation gate

A later activation PR must re-check Gravatar's current official documentation and terms and must not proceed unless all of the following are true:

1. PersonaLattice has an accessible privacy-policy disclosure satisfying the provider's current API requirements.
2. A free server-side Gravatar API key can be configured outside Git without creating a paid baseline dependency.
3. The adapter remains bounded to the reviewed Profiles endpoint, request budget, timeout, response-size ceiling and minimal retained fields.
4. Missing key, not found, rate limit, malformed result and provider-unavailable outcomes map through the existing typed source-run contract without guessing execution state.
5. Source catalog, binding, provider registry and shared `ProviderRuntime` ownership are activated atomically.

## Consequences

Positive:

- the email-hash derivation and response-admission rules are testable before any external call exists;
- the planned integration cannot silently expand retained profile data just because the upstream API exposes it;
- zero-spend remains possible because the current provider offers a free API tier;
- provider terms, rather than implementation convenience, determine when activation is allowed.

Costs:

- Gravatar remains unavailable until the privacy-policy and server-side free-key requirements are satisfied;
- the current planned source-capability declaration remains non-executable and must be reconciled with the final admitted field set during activation.

## Non-goals

This decision does not create a universal email-account existence checker, add avatar collection, follow verified-account links, add contact/payment data, or activate any provider call.
