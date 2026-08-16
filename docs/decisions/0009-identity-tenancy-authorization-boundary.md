# ADR 0009 — single-admin authentication and private case access

## Status

Accepted for M7 implementation. The earlier multi-tenant draft of this ADR is superseded by this one-admin product decision.

## Context

PersonaLattice is currently a private personal investigation workbench operated by one administrator. Building tenants, teams, invitations and role hierarchies now would add attack surface and persistence complexity without serving the actual product.

The public deployment may expose a product preview and synthetic evidence dashboard, but real-person intake, provider execution and stored case data must remain unavailable until a server-validated admin session exists. A blurred UI is not authorization: the unauthenticated browser must not receive the protected payload at all.

The product processes potentially sensitive public-source and operator-authorized evidence. Session theft, cross-site request forgery, accidental public serialization, arbitrary object access and unbounded upload parsing are therefore release-blocking security failures.

## Decision

M7 uses one configured administrator identity and a narrow server-side session boundary.

1. There is no public registration, invitation, team, tenant or role model in M7.
2. The admin username and Argon2id password hash are deployment secrets. Plaintext passwords are never committed or stored.
3. Successful login creates a high-entropy opaque bearer session token. Only its SHA-256 hash and server-side session record are retained; downstream authorization never receives the browser bearer secret.
4. The browser session cookie is HttpOnly and SameSite=Strict and is Secure in production. It contains no cleartext personal information.
5. Every unsafe authenticated request carries an independent per-session CSRF token in `X-PersonaLattice-CSRF`; the server compares it against the session record before performing the operation.
6. Logout, expiry, revocation, process restart or an invalid/tampered token fail closed.
7. Login failures are rate-limited per observed request source. This is defense-in-depth, not a substitute for edge/platform rate limiting.
8. Protected read and write dependencies are centralized. Knowing a case UUID or endpoint path never grants access.
9. The public web root renders synthetic placeholders only. The private operator route is intentionally absent from public navigation, but route obscurity is not relied upon for security.
10. Browser-to-API calls use a same-origin Next.js `/api` proxy so the HttpOnly session cookie and CSRF model do not depend on permissive cross-site credential behavior.
11. Stored research cases are private admin-only objects. They have explicit retention expiry and delete operations. Initial local persistence is SQLite; production deployment requires persistent storage and a single API worker unless sessions are moved to shared durable storage.
12. Provider results and upload metadata remain bounded and allowlisted. Internal objects are not generically serialized.
13. JPEG and PNG uploads are parsed only for bounded file and EXIF metadata in M7. Embedded GPS, when present, is labeled as historical embedded metadata rather than current/live location. No face identification is performed.
14. M5 semantics remain unchanged: correlation is deterministic evidence-strength triage, `calibration_status` remains uncalibrated, `is_identity_claim` remains false, and contradictions/stale evidence stay visible.

## Current research capability boundary

The authenticated product can execute the approved public-source path rather than merely preview it:

- usernames: governed Sherlock discovery on the reviewed site allowlist plus allowlisted public GitHub profile fields;
- phones: normalization and numbering-plan/carrier/region/time-zone metadata only, not subscriber identity;
- emails: normalization and domain evidence only until an external enrichment provider passes source/legal/cost review;
- public URLs: canonical URL metadata only until a hardened SSRF-safe fetcher/provider is approved;
- PDF/text/JPEG/PNG uploads: bounded extraction/metadata review; extracted candidates never autonomously trigger outside research.

A result that is not supported by an attributable source remains unknown. PersonaLattice does not obtain private-account content, bypass credentials, probe account recovery, evade access controls, covertly discover a subject's IP/device location or perform Internet-scale face recognition.

## Consequences

- The architecture is materially simpler than a premature SaaS tenant model while still failing closed for protected data.
- In-memory sessions intentionally invalidate on restart and require a single backend worker for the first deployment. Multi-worker scale requires shared session storage first.
- SQLite is acceptable for the one-operator initial deployment only when mounted on persistent protected storage; it is not a serverless-ephemeral database strategy.
- Public presentation and protected data transport are cleanly separated.
- M8 can add privacy lifecycle, stronger audit evidence and deployment-hardening without having to unwind a speculative multi-user model.
- Future conversion to a multi-user product requires a new ADR rather than silently stretching the one-admin authorization assumption.
