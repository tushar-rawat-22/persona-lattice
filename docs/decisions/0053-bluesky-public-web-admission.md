# ADR 0053 — Bluesky public-web admission is fail-closed

Status: accepted as an activation preflight; Bluesky remains non-executable

## Context

Bluesky is the first post-V2-D source candidate. Its public AppView exposes
`app.bsky.actor.getProfile` without authentication, and Bluesky recommends
`https://public.api.bsky.app` for unauthenticated public requests. That makes the
profile endpoint compatible with PersonaLattice's zero-spend baseline: no API
credential, paid proxy or paid enrichment service is required.

Two details make a direct activation unsafe.

First, PersonaLattice's `username` lead kind is broader than an AT Protocol
handle. AT Protocol handles are DNS-hostname-shaped identifiers with at least two
labels. Querying every generic username against Bluesky would be speculative
spraying rather than source-scoped enrichment.

Second, Bluesky defines the global `!no-unauthenticated` label to make content
inaccessible to logged-out users in applications that respect the label. A
profile returned with that signal cannot be treated as an ordinary public-web
observation. It is also not "not found": the source was contacted and returned a
visibility decision.

Official material reviewed on 2026-08-19:

- AT Protocol `app.bsky.actor.getProfile` lexicon: the endpoint does not require
  authentication and accepts an AT identifier;
- Bluesky API directory: public AppView requests should prefer
  `https://public.api.bsky.app`;
- AT Protocol handle specification: handle syntax, lowercase normalization and
  reserved/non-public TLD restrictions;
- Bluesky moderation guide: `!no-unauthenticated` semantics;
- Bluesky Terms of Service, last updated 2025-08-14.

## Decision

Add a local, network-free admission contract before registering or binding a
Bluesky provider.

The contract:

- accepts only syntactically valid, real-world AT Protocol handles;
- normalizes handles to lowercase;
- rejects generic usernames, `@`-prefixed UI forms and reserved/non-public TLDs
  before any future provider call;
- requires returned profile handle and requested handle to match;
- requires a bounded DID-shaped identifier;
- validates the returned label structure fail-closed;
- raises a distinct public-web opt-out outcome for
  `!no-unauthenticated` instead of mapping it to not-found;
- admits only DID, normalized handle and optional display name plus explicit
  account-candidate/non-identity flags;
- does not retain description, avatar, follower/follow counts, post counts,
  viewer state or arbitrary unexpected fields.

This block deliberately does **not** add a provider descriptor, source binding,
shared-runtime owner or network call. `bluesky_public_profile` remains `PLANNED`,
source-policy-unreviewed for execution, and non-recursive until the next adapter
block proves HTTP/error semantics and typed source-run mapping.

## Required activation follow-up

Before Bluesky can become executable, one bounded adapter change must still prove:

1. only the public `app.bsky.actor.getProfile` AppView route is called;
2. not-found is distinguished from suspension/deactivation and malformed output;
3. remote rate limits and transient failures use the existing provider errors;
4. `!no-unauthenticated` becomes a typed **attempted** public-web opt-out state,
   not not-found and not a provider reliability failure;
5. success, not-found, opt-out, malformed, rate-limit and unavailable fixtures are
   deterministic;
6. catalog, binding, registry and process-wide `ProviderRuntime` ownership become
   consistent in the same activation PR.

Production recursion remains depth 2 / 12 nodes. M5 remains uncalibrated
strength-of-evidence triage and does not become identity probability.

## Consequences

The next activation block is slightly larger because source-state vocabulary must
represent a successful-but-withheld public-web lookup. That is preferable to
contaminating `not_found` or provider-failure metrics merely to add a source
faster.
