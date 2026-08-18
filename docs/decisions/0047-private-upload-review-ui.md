# ADR 0047 — Private upload review UI uses server-owned candidate state

Status: accepted for V2-D operator workflow visibility

## Context

The backend already supports a complete reviewed-document chain: bounded file preview, short-lived server-owned candidates, authenticated and CSRF-protected confirm/reject/reopen/promote actions, and a separate explicit action that starts a retained research case from the current server-owned candidate.

The private admin page still showed only artifact-level counts. An operator could not exercise the reviewed-candidate workflow from the product UI even though the backend boundary was complete.

## Decision

Add a private upload-review component to the existing admin intake result.

The browser may display the candidate value returned by the authenticated file-preview response, but that value is never sent back as authorization state. Review mutations and promotion identify the server-owned record only by artifact ID and candidate ID. The API reloads the current candidate before applying the requested action.

Confirmation, rejection and re-review remain distinct from promotion. Promotion remains a lead preview and does not execute a provider. Starting research remains a separate explicit action and sends only the selected case mode plus the current intake purpose/consent acknowledgement; the reviewed identifier is reloaded server-side immediately before execution.

The UI treats returned review state as display state only. It does not reproduce candidate eligibility, provider policy, normalization or evidence semantics in browser code.

## Consequences

Positive:

- the existing document-review backend is usable from the private operator console;
- no browser-supplied identifier becomes review or execution authority;
- provider execution remains visibly separated from confirmation and promotion;
- the workflow continues to use the existing local database and zero-spend baseline.

Costs:

- the previewed candidate value remains visible in browser memory for the active authenticated intake, as it already was;
- a case created from the review panel is reported by ID there; deeper retained-case inspection continues through the existing case UI.

## Non-changes

This does not activate a provider, add a credential, change recursion limits, expand retention, alter M5 semantics, or make any paid service required.
