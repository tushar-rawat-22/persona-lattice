# ADR 0038 — Upload review mutations use server-owned HTTP actions

Status: accepted for V2-D architecture closure

## Context

File preview already persists short-lived review candidates in SQLite, and the review service already owns atomic confirm, reject, reopen and promotion operations. The remaining gap is HTTP exposure for the private operator UI.

Accepting a candidate value, identifier kind or provenance from the browser would reopen the client-tampering problem that the server-owned review store was introduced to remove. Promotion also must not become an implicit provider call: it is only the transition from a confirmed document candidate into the typed lead contract.

## Decision

Expose four authenticated write actions under `/v1/files/review/{artifact_id}/{candidate_id}`:

- `POST .../confirm`
- `POST .../reject`
- `POST .../reopen`
- `POST .../promote`

Every action uses the existing one-admin session and CSRF dependency. The browser supplies only the artifact UUID and candidate UUID. Candidate value, identifier kind, review state and provenance are reloaded from the server-owned review store.

Review-state responses deliberately omit the candidate value. They return only the identifiers needed to address the record, candidate/identifier kind, review state, research-authorization flag and page/character provenance. Promotion returns the typed reviewed lead, including its normalized value and provenance-bearing `artifact://` locator, but does not schedule or execute provider research.

Missing or expired candidate records return 404. Promotion of a candidate that is not currently confirmed and research-authorized returns 409.

Successful review actions write privacy-bounded audit events. Audit details include only candidate/lead type metadata and do not copy identifier values, artifact UUIDs, candidate UUIDs, source locators, document text or file metadata.

## Consequences

Positive:

- browser state cannot authorize research or rewrite document provenance;
- the existing CSRF/session boundary applies unchanged;
- review mutations and HTTP mutations share one server-side authority;
- promotion remains a typed state transition rather than a hidden network side effect;
- audit records show operator actions without duplicating the reviewed identifier.

Costs:

- four explicit endpoints add a small API surface;
- the private UI still needs a later wiring block to render and call these actions;
- promoted leads are returned to the operator but are not yet attached to a new case/run automatically.

## Boundaries unchanged

This decision adds no third-party provider, credential, paid dependency, raw-document retention, recursion-limit increase, identity probability, private-account bypass or automatic external lookup.

## Next gate

Wire the private operator UI to these bounded actions, then define the explicit operator step that moves a promoted reviewed lead into a chosen research/case run. That step must remain separate from candidate confirmation and must preserve the zero-spend baseline.
