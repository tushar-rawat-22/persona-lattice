# ADR 0065 — WebFinger requires an explicit profile-URL admission boundary

Status: accepted pre-activation design

## Context

PersonaLattice already carries a planned `webfinger_activitypub` source, but the existing catalog entry is broader than what RFC 7033 alone proves. WebFinger returns a JSON Resource Descriptor (JRD) containing a subject, aliases, properties and links. It does not by itself establish a display name, and converting an `acct:` subject into a generic PersonaLattice username would discard the federation domain that makes the identifier meaningful.

The standard also makes the query host security-sensitive: the client sends an HTTPS request to `/.well-known/webfinger` on the host associated with the query target. Accepting an arbitrary URL without a preflight boundary would create an avoidable SSRF and local-network risk.

## Decision

Add a network-free WebFinger admission module before any provider activation.

The preflight:

- accepts only an explicit absolute HTTPS profile URL;
- rejects credentials, explicit ports, query strings, fragments, root-only URLs and well-known endpoints as profile seeds;
- rejects IP literals, single-label hosts and common local-use host suffixes;
- normalizes the DNS hostname through IDNA and constructs the RFC 7033 query on that same host;
- requires a returned JRD to be anchored to the requested profile URL through either `subject` or `aliases`;
- admits only HTTPS `self` and `profile-page` link targets;
- bounds the number and size of admitted links;
- does not interpret JRD properties as names or other personal attributes;
- does not convert an `acct:` subject into a generic username lead.

The source remains `PLANNED`, unbound and non-recursive. This block performs no DNS lookup and no network request.

## Source-policy review

RFC 7033 requires WebFinger queries to use HTTPS and defines the well-known path, `resource` parameter and JRD response. The query host should match the host portion of the query target unless separately directed. Mastodon's current WebFinger documentation illustrates the same model for federated profiles and shows `profile-page` and ActivityPub `self` links.

The protocol itself has no paid service requirement or API credential. Individual federated servers can still have their own availability and operator policies, so future activation must remain bounded and must not assume universal support.

## Catalog correction required before activation

The current planned catalog declaration says `webfinger_activitypub` may emit URL, username and name leads. That is too broad for WebFinger alone.

Before activation, either:

1. narrow the executable WebFinger capability to URL output only; or
2. split ActivityPub actor fetching into a separate reviewed network capability with its own payload, SSRF, content-type, size and retention rules.

Do not activate the current combined declaration unchanged.

## Consequences

Positive:

- arbitrary URLs cannot directly become WebFinger network targets;
- local/IP targets fail before network I/O;
- response admission stays tied to the explicit profile resource;
- federation-domain information is not lost by manufacturing a generic username;
- the zero-spend baseline remains intact.

Costs:

- WebFinger remains non-executable until the catalog/output model is corrected and an adapter has deterministic success, not-found, malformed, rate-limit/unavailable and redirect/SSRF fixtures;
- ActivityPub actor enrichment remains a separate future decision rather than being implied by this preflight.

## Next gate

Correct the catalog output contract, define redirect handling that cannot escape to private/local targets, and implement one governed WebFinger adapter through the existing `ProviderRuntime`. ActivityPub actor fetching must not be bundled into that activation without its own review.
