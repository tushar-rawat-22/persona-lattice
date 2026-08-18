# ADR 0037 — Upload review mutations operate on server-owned candidate state

Status: accepted for V2-D architecture closure

## Context

PR #60 made extracted upload candidates short-lived server-owned records. The next risk is mutation semantics: confirm, reject and re-review actions must not read a candidate from the browser and write it back as authorization state. Concurrent operator requests also must not overwrite one another with stale copies.

## Decision

Add a server-side upload review mutation service over `UploadReviewStore`.

The store now exposes one atomic mutation operation that:

- looks up the exact artifact ID and candidate ID inside a SQLite `BEGIN IMMEDIATE` transaction;
- treats missing and expired candidates as absent;
- supplies the current server-owned `ReviewCandidate` to an internal transform;
- permits changes only to `review_status` and `external_research_authorized`;
- rejects any transform that changes the candidate value, identifier kind, candidate/artifact IDs, origin, type, page number or character provenance;
- persists the mutation before releasing the transaction.

The review service provides four operations over identifiers only:

- confirm: mark the current stored candidate confirmed and, for identifier candidates, authorize external research;
- reject: mark it rejected and revoke research authorization;
- re-review: return it to pending and revoke research authorization;
- promote: load the current stored candidate and pass it through the existing reviewed-document promotion contract.

The service never accepts a browser-supplied `ReviewCandidate` as authority.

## Why the HTTP routes are separate

This block establishes the mutation authority before exposing it through FastAPI. Authentication, CSRF checks, response contracts and audit events belong to the HTTP boundary and can now call a small service that already fails closed on candidate ownership and provenance.

Keeping the two concerns separate also makes it possible to test review-state semantics without constructing authenticated HTTP requests.

## Consequences

Positive:

- browser tampering cannot alter the value or provenance being approved;
- concurrent review mutations serialize at the local SQLite boundary;
- rejection or re-review immediately removes promotion authorization;
- promotion reuses the existing typed lead contract and artifact/candidate provenance;
- the zero-spend baseline remains the existing local SQLite database.

Costs:

- review mutations now take a short database write lock;
- the authenticated, CSRF-protected operator routes are still the next block;
- promotion returns a reviewed lead but still does not execute a provider or change recursion policy.

## Deliberate non-changes

This decision does not add a network provider, paid service, credential, new retained document content, recursion expansion, identity-probability semantics or browser-accessible review endpoint.
