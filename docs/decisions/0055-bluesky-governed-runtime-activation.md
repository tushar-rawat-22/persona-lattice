# ADR 0055 — Bluesky public profiles activate only for valid AT handles

Status: accepted for reviewed source activation

## Context

PersonaLattice already had a bounded Bluesky public-profile adapter and a pre-network admission contract, but the source remained planned and non-executable. Activation therefore had to connect the existing adapter to the closed V2-D execution chain without turning every generic username into a Bluesky request.

Bluesky's official public AppView exposes `app.bsky.actor.getProfile` without authentication. For public-web clients, Bluesky recommends the cached `https://public.api.bsky.app` host. AT handles are DNS-style identifiers, and the `!no-unauthenticated` label is an explicit public-web/logged-out opt-out signal.

The source review also checked Bluesky's current general Terms of Service and AT Protocol Network Services privacy notice. The terms were last updated August 14, 2025; the network-services privacy notice describes profiles and user content as publicly available in the decentralized network. That public status does not override explicit public-web opt-out or authorize collection of nonpublic data, so PersonaLattice keeps the narrower AppView/visibility contract below.

A PersonaLattice `username` is broader than an AT handle. Treating a plain value such as `alice` as Bluesky-applicable would manufacture provider traffic and misleading source outcomes for a source that was never sufficiently scoped.

## Decision

Activate `bluesky_public_profile` as a reviewed, zero-direct-cost governed source, but keep value-level applicability in the quick-research boundary.

The activation:

- changes the source capability to active/reviewed/recursive-eligible;
- registers the provider as development status with no credential requirement;
- binds the source to the existing governed adapter boundary;
- registers the exact adapter instance in the process-wide `ProviderRuntime`;
- calls Bluesky only when the normalized username passes the existing AT-handle admission contract;
- makes a plain or malformed username non-applicable before any provider execution, with no fabricated source-run record;
- keeps public-web opt-out and suspended/deactivated account responses as attempted neutral `withheld` outcomes rather than failures or `not_found`;
- keeps all other execution outcomes on the existing typed source-run mapping;
- retains only DID, normalized handle and optional display name plus account-candidate/non-identity/public-visibility flags.

The catalog `emits` declaration is narrowed to `username` and `name`. The adapter does not admit location, and its source locator is provenance rather than an automatically emitted URL lead.

## Runtime policy

The provider uses one attempt, a four-second timeout, a 64 KiB result ceiling, concurrency two and a local 30-per-60-second application budget. The local budget is a PersonaLattice safeguard, not a claim about a fixed upstream Bluesky quota.

No API key, OAuth token or paid service is required. If Bluesky is unavailable, the rest of the zero-spend research path continues.

## Consequences

Positive:

- a reviewed zero-cost public source is added without reopening the V2-D architecture;
- generic username spraying into Bluesky is avoided;
- public-web visibility choices stay out of provider-failure metrics;
- catalog, binding, provider registry and process runtime ownership remain covered by the existing cross-layer CI invariant;
- the retained evidence remains an account candidate and never an identity claim.

Costs and limits:

- valid AT-handle lookups add one bounded provider call to username research;
- the first activation executes that call after the existing public-profile enrichments rather than adding more concurrency to an already parallel block;
- kind-level source planning can report Bluesky as current username coverage even though actual applicability remains value-dependent; callers must not interpret the planner as proof that every username value is queryable by every source.

## Deliberately unchanged

- production recursion stays at depth 2 / 12 nodes;
- M5 stays uncalibrated evidence-strength triage with `is_identity_claim=false`;
- no biography, avatar, follower/follow/post counts, viewer state or arbitrary response fields are retained;
- no private-account bypass, login probing, credential collection, covert tracking or paid baseline dependency is added.
