# ADR 0012 — Source capability catalog before provider expansion

Status: accepted for V2 infrastructure

## Context

PersonaLattice now has a typed evidence-lead graph and deterministic frontier.
The next temptation is to add many APIs directly to the research runner. That
would optimize for short-term coverage at the cost of long-term control: source
availability, accepted seed kinds, emitted lead kinds, credentials, pricing,
terms review and recursive eligibility would become scattered across adapter
code.

A large evidence-intelligence product needs to know what sources are *capable* of
before it decides what is *allowed* to run.

## Decision

Add a static source capability catalog that is separate from provider execution.

Every logical source declares:

- accepted lead kinds;
- possible emitted lead kinds;
- lifecycle status (`active`, `optional`, `planned`, etc.);
- source mode (local, governed provider, public API, licensed search, open
  standard, user-authorized, manual);
- broad cost class;
- credential class;
- whether current source policy has been reviewed;
- whether the source is eligible for recursive execution;
- deterministic planning priority;
- an explanatory note for material limitations.

A catalog match is never execution authority. The existing provider/research
layer must still enforce adapter existence, purpose/consent, credentials, rate
budgets, timeouts, response ceilings and source-specific policy immediately
before a call.

## Planned is not executable

Planned sources may appear in architecture/planning queries so the operator can
see the intended expansion path. They are never returned by a
`recursive_only=True` planning query and cannot declare `recursive_eligible=True`.

A planned source becomes active only after:

1. current official documentation and terms/source-policy review;
2. a bounded adapter exists;
3. fixture tests cover success, not-found, malformed, rate-limited and unavailable
   responses;
4. exact emitted fields have been reviewed against the lead extractor;
5. server-side credential handling is defined where needed;
6. cost/rate ceilings are explicit;
7. the provider execution gate admits the source.

This prevents architecture documentation from accidentally becoming live
collection authority.

## Zero-spend planning

The user's current operating constraint is to avoid paid infrastructure/API spend
where possible. The catalog therefore exposes a computed `zero_spend_eligible`
planning hint.

It is intentionally derived from cost and credential classes rather than stored
as an independent boolean, so contradictory declarations cannot drift apart.
It means only that the current catalog does not require a paid credential/service
tier for that source. It is not a permanent pricing promise. Source pricing,
quotas and terms are rechecked immediately before activation and periodically
thereafter.

Metered sources can remain optional without contaminating a zero-spend research
plan.

## Initial catalog

Active/optional logical sources describe current private-V1 behavior:

- local normalization;
- libphonenumber numbering-plan metadata;
- reviewed Sherlock username discovery;
- GitHub, GitLab and Codeforces public profile APIs;
- public DNS infrastructure metadata;
- optional licensed Brave exact-public-web search.

V2 integration targets are catalogued as planned, not executable:

- Bluesky public profiles;
- Gravatar public profiles from an already-known email identifier;
- WebFinger/ActivityPub federation resolution from a sufficiently scoped
  federated resource/profile URL;
- RDAP domain registration metadata that the authoritative service actually
  exposes;
- user-authorized Google People imports.

## Important source-specific constraints

### Bluesky

The public AppView exposes many unauthenticated public endpoints and profile
lookup accepts a DID or handle. A future adapter must still define exact handle
semantics and source fields before activation. The catalog does not treat an
arbitrary username from another platform as proof of a Bluesky identity.

### Gravatar

A future adapter starts only from an already-known/authorized email. The email is
normalized according to Gravatar's documented hashing rule and represented to the
remote API by its SHA-256 identifier. Production use should keep any API key
server-side. Profile results are public profile evidence, not proof that every
other same-name account belongs to the same person.

### WebFinger / ActivityPub

WebFinger requires a query target and a meaningful host. A generic username does
not identify which domain should receive the query. PersonaLattice therefore does
not spray a username across arbitrary federation servers. A future adapter starts
from a recognized federated resource or profile URL and keeps the returned JRD/
actor links as provenance-bearing observations.

### RDAP

RDAP provides standardized access to registration data, but registration fields
may be redacted or withheld. A missing registrant field is not a failure to
"unmask" somebody and must not trigger attempts to obtain nonpublic registration
data through other means.

### User-authorized imports

Google People and similar integrations belong to a different trust class from
public-source research. They require explicit OAuth scope, token lifecycle,
revocation and audit design before activation and are never represented as
universal people-search databases.

## Consequences

Positive:

- provider/API work can be sequenced without rewriting orchestration;
- zero-spend and metered plans can be separated deterministically;
- planned integrations cannot execute accidentally;
- the operator can see coverage gaps by lead kind before buying or building an
  adapter;
- source-policy and credential requirements become reviewable architecture data;
- future UI can distinguish "we do not support this source" from "the source was
  executed and returned not found."

Costs:

- catalog metadata must be maintained when a source's policy/pricing changes;
- activation requires an explicit catalog transition plus adapter review;
- the catalog duplicates a small amount of descriptive metadata from provider
  adapters.

That duplication is intentional. The catalog answers planning/capability
questions; provider descriptors answer execution questions. They must agree
before activation, and future consistency tests will enforce that relationship.
