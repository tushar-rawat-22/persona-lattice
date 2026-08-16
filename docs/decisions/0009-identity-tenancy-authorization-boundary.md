# ADR 0009 — identity, tenancy and authorization before production case access

## Status

Accepted for M7 implementation.

## Context

M6 intentionally stopped at a local/synthetic evidence dashboard. PersonaLattice
still has no production endpoint that lists or reads stored personal cases. M7
must establish the access-control boundary before that changes.

Authentication answers who controls a session. It does not answer whether that
principal may access a particular case/evidence object or invoke a privileged
function. PersonaLattice therefore must not treat possession of an object UUID,
a route name or an authenticated session as authorization.

The system contains identity/evidence data with higher abuse and privacy impact
than an ordinary content application. Cross-user or cross-tenant object access,
privilege escalation and over-broad serialization would be structural failures,
not UI bugs.

## Decision

M7 separates authentication, session handling and authorization into explicit
server-side responsibilities and keeps production stored-case access disabled
until they are proven together.

1. The server derives an authenticated principal from a validated session. No
   browser-supplied user ID, tenant ID, role or ownership field is trusted as an
   authorization fact.
2. A principal has a stable internal subject identifier plus explicit membership
   and role bindings. Authentication state and application authorization state
   remain distinct.
3. Authorization is centralized, deny-by-default and action-oriented. Access is
   granted only when a policy explicitly permits a principal to perform an
   action on a resource in the relevant tenant/ownership context.
4. Object-level authorization runs whenever client-controlled input selects or
   acts on a persisted object. Random UUIDs remain useful identifiers but are
   not an access-control mechanism.
5. Function-level authorization is explicit for privileged/admin operations;
   ordinary authenticated principals do not inherit access merely because an
   endpoint exists.
6. Future browser/API response models continue to cherry-pick bounded fields.
   Internal ORM/database objects are not generically serialized.
7. Session material must not contain cleartext personal case information. The
   chosen browser session mechanism must use secure transport/cookie settings,
   explicit expiry/inactivity policy and logout invalidation appropriate to the
   selected architecture.
8. Authorization decisions expose structured, public-safe reason codes for
   deterministic tests and later audit integration without logging secrets or
   unnecessary personal data.
9. Deterministic synthetic tests must cover anonymous denial, same-owner allow,
   cross-user denial, cross-tenant denial, role/function denial, identifier
   tampering, invalid/expired session handling and explicit privileged grants.
10. No stored-case production read/list endpoint is enabled merely to test the
    authentication layer. The object-access surface is introduced only after the
    authorization core and its negative tests are green.
11. M7 does not change M5 correlation semantics, make an identity claim, expand
    providers, add report sharing/export or introduce regulated decision flows.
12. Retention/deletion, jurisdiction-specific privacy lifecycle and broader
    abuse governance remain separate M8 work so M7 does not become an
    unreviewable security catch-all.

## Implementation shape

The initial M7 implementation should prefer a small framework-neutral domain
layer over route-specific permission conditionals:

- authenticated-principal type;
- tenant/membership/role types;
- resource/action vocabulary;
- centralized authorization decision service;
- explicit allow/deny reason codes;
- synthetic policy fixtures and negative tests;
- adapter boundary for whichever authentication/session mechanism is selected.

FastAPI routes and Next.js UI should consume this boundary rather than implement
parallel authorization logic.

## Security basis

The design follows three current principles that are directly relevant to
PersonaLattice:

- object identifiers must be checked against the authenticated principal's
  permission for the requested object;
- privileged functions should deny access by default and require explicit
  grants;
- authenticated sessions need bounded lifetime, secure session-secret handling
  and explicit logout/invalidations.

These correspond to OWASP API1:2023 Broken Object Level Authorization, OWASP
API5:2023 Broken Function Level Authorization and NIST SP 800-63-4 session
management guidance.

## Consequences

- M7 may initially add substantial tests and policy code without exposing a new
  end-user case feature; that is intentional.
- Authentication-provider choice can change without rewriting application
  authorization semantics if the principal adapter remains narrow.
- Future case APIs have one place to ask authorization questions instead of
  duplicating fragile route-level checks.
- Negative authorization tests become a release gate before real personal-data
  access exists.
- M8 can build retention, deletion, audit and abuse governance on a known
  principal/resource/action model rather than inventing identity semantics
  again.
