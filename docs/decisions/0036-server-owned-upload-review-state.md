# ADR 0036 — Upload review decisions use server-owned candidate state

Status: accepted for V2-D architecture closure

## Context

`/v1/files/preview` already performs bounded extraction and returns review-only candidates, but the preview response is sent to the browser. A later confirm/reject endpoint must not accept the browser's copy of a candidate as authority: values, identifier kinds, artifact IDs, page numbers and character offsets are all client-tamperable once they leave the API.

The reviewed-lead promotion contract from ADR 0034 therefore needs a short-lived server-side source of truth before operator actions can be exposed safely.

## Decision

Successful file preview now stores each extracted `ReviewCandidate` in a short-lived SQLite review table keyed by candidate ID and artifact ID.

The store:

- uses the existing `PERSONALATTICE_DB_PATH`; no new service or paid dependency is introduced;
- retains the normalized candidate value plus candidate/artifact IDs, identifier kind, review state, and mechanically derived page/character provenance;
- does not copy uploaded file bytes, filenames, hashes, surrounding extracted text or complete document text into review state;
- validates that the candidate payload's candidate/artifact IDs still match the database row before returning it;
- requires both artifact ID and candidate ID for lookup;
- expires review candidates after 24 hours by default;
- allows a bounded 1–168 hour retention window through `PERSONALATTICE_UPLOAD_REVIEW_RETENTION_HOURS`;
- purges expired rows opportunistically on preview/list/get operations.

`ArtifactPreview.storage_retained=false` continues to mean the uploaded artifact itself is not retained. Short-lived candidate review metadata is a separate server-side authorization record and is deliberately bounded more tightly than retained research cases.

## Why this precedes review endpoints

A confirm/reject endpoint built directly over a browser-supplied `ReviewCandidate` would only appear to provide human authorization. A caller could alter the candidate value or provenance and then ask the server to approve the altered object.

The review API must instead accept identifiers for server-owned state, load that state, apply `confirm_candidate()` or `reject_candidate()`, persist the resulting review state, and call `promote_confirmed_identifier_candidate()` only from the server-owned confirmed record.

## Deliberate non-changes

This block does not:

- add a confirm/reject/promotion HTTP endpoint;
- execute a promoted lead or call any provider;
- retain raw uploaded files or full extracted document text;
- add a third-party service, credential or paid dependency;
- change recursion limits or M5 identity semantics.

## Consequences

Positive:

- future operator review can be bound to the exact candidate the server extracted;
- browser-supplied values and provenance no longer need to be trusted as authorization state;
- review state survives the preview response without retaining whole documents;
- the zero-spend baseline remains local and self-contained.

Cost:

- normalized candidate values now have a bounded server-side review lifetime instead of disappearing immediately after preview;
- review-state deletion and expiry become part of the privacy lifecycle;
- the next block still needs authenticated/CSRF-protected confirm, reject, re-review and promotion endpoints using this store.
