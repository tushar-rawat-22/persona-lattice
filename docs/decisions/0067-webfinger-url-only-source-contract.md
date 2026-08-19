# ADR 0067 — WebFinger remains a URL-link source

Status: accepted for pre-activation source review

## Context

The planned source key `webfinger_activitypub` predates the current source-admission work. Its catalog entry claimed that one lookup could emit URL, username and name leads.

That claim is too broad for RFC 7033 alone. A WebFinger response is a JRD containing a subject, aliases, properties and links. It does not by itself establish a generic cross-service username or a display name. Converting a federated identity such as `acct:alice@example.com` into the generic username `alice` would discard the federation domain and could make later recursion query unrelated services.

ActivityPub actor retrieval is also a different network operation. It has its own response schema, content and SSRF considerations and has not been reviewed as part of the WebFinger transport work.

## Decision

Keep the historical `webfinger_activitypub` source key for compatibility, but narrow its planned capability to:

- accept explicit URL leads only;
- emit URL leads only;
- remain `PLANNED`, unbound and non-recursive until activation is separately reviewed;
- treat the source as WebFinger public-link resolution only.

The source key is not permission to fetch an ActivityPub actor. ActivityPub actor retrieval must be represented and reviewed as a separate capability before it can execute.

The existing WebFinger admission layer continues to admit only bounded HTTPS `self` and `profile-page` links anchored to the requested resource. It does not manufacture username or name leads.

## Why the source key is not renamed now

Renaming the logical source during pre-activation review would create avoidable migration churn across planning, documentation and historical references without changing executable behavior. The compatibility name is therefore retained, while its note and tests make the narrower meaning explicit.

A future cleanup may rename the source if there is a real operator or maintenance benefit, but source semantics must not depend on that rename.

## Cost and policy boundary

WebFinger is an open protocol and requires no PersonaLattice API credential or paid service. That does not make every arbitrary server an automatically approved source. Individual servers can impose access controls or different response policies, and RFC 7033 explicitly permits authentication requirements.

This ADR therefore does not activate network execution. Activation still requires a reviewed decision about the host/applicability policy in addition to the already-built HTTPS, DNS and redirect protections.

## Consequences

Positive:

- the catalog no longer overstates what WebFinger alone can establish;
- generic usernames and names cannot enter the recursive graph from WebFinger metadata;
- ActivityPub actor fetching cannot ride through the WebFinger source key without a separate review;
- the zero-spend baseline is unchanged.

Cost:

- the historical source key remains slightly broader in name than in executable intent, so the compatibility note and regression test remain necessary.

## Next gate

Before activating WebFinger, decide and test a defensible applicability/host-policy rule, then wire the URL-only source atomically through source binding, provider registry, shared `ProviderRuntime`, typed source-run reporting and canonical observations. Do not add ActivityPub actor fetching in that activation block.
