# ADR 0068 — WebFinger uses time-bounded exact-host source policy

Status: accepted for pre-activation source review

## Context

The WebFinger URL parser and SSRF-safe transport are not enough to authorize execution. RFC 7033 allows a WebFinger resource to require authentication, return different information to different clients, and delegate to a hosted service. A syntactically valid public hostname therefore does not prove that PersonaLattice has reviewed that host as a source.

The source also cannot be made safe by approving a software family or wildcard domain. Independent fediverse servers can have different operators, policies, privacy practices and access rules.

## Decision

Add an exact-host source-policy gate in front of any future WebFinger execution.

A host approval:

- names one lowercase hostname exactly;
- has an explicit review date and expiry date;
- carries a concrete rationale for why unauthenticated public WebFinger use is acceptable;
- never implies approval for sibling hosts or subdomains;
- expires until the host's current source terms/privacy posture is reviewed again.

The production approval registry is intentionally empty in this block. `webfinger_activitypub` remains planned, unbound and non-recursive. The new gate is infrastructure for a later host-specific review, not permission to make a network request.

Existing URL admission and network controls remain separate. A host must first pass URL/hostname admission and later, if activated, still pass fresh DNS/global-address admission and IP-pinned HTTPS immediately before every request and redirect hop.

## Why not approve arbitrary WebFinger hosts

RFC 7033 defines protocol behavior; it does not make every implementation one homogeneous source. It explicitly permits authenticated and client-dependent responses. Treating all conforming-looking hosts as reviewed would collapse protocol safety, source policy and operator terms into one assumption.

## Consequences

Positive:

- activation cannot silently widen from one reviewed server to an entire software ecosystem;
- source-policy review becomes time-bounded rather than permanent by accident;
- a hostname remains independently revocable without changing the protocol parser or transport;
- future CI can prove the exact approved host set.

Costs:

- WebFinger coverage grows host by host unless a future review establishes a stronger, defensible policy class;
- source activation remains blocked until at least one real host is reviewed and added deliberately.

## Next gate

Review one concrete WebFinger host using current primary terms/privacy/source documentation. If it passes, add that exact host and then activate WebFinger atomically through source catalog, binding, provider registry, shared `ProviderRuntime`, quick research, typed source-state reporting and canonical evidence. Do not use wildcard approvals as a shortcut.
