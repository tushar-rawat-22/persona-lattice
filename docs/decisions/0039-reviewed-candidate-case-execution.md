# ADR 0039 — Reviewed document candidates require a separate case-execution action

Status: accepted for V2-D closure

## Context

PR #64 exposed authenticated review actions for server-owned upload candidates. A confirmed candidate can be promoted into a typed lead, but promotion intentionally stops before provider execution.

The remaining gap is the transition from that reviewed lead into a retained research case. Reusing the generic case endpoint from the browser would lose the fact that the identifier was authorized through document review and would allow the client to present an arbitrary identifier as though it came from a reviewed upload.

## Decision

Add a separate authenticated, CSRF-protected `run-case` action under the existing upload-review route. The request carries artifact/candidate IDs in the path plus only research mode, purpose and consent acknowledgement in the body.

Immediately before execution, the service:

1. enforces the requested purpose/consent policy;
2. reloads the current server-owned candidate by artifact ID + candidate ID;
3. reuses the existing promotion contract, which requires a confirmed, externally research-authorized executable identifier;
4. derives the research kind and normalized seed from that trusted lead;
5. executes either the existing quick or converged research path;
6. writes one retained case with the reviewed-upload source locator attached as seed provenance.

The action returns case metadata, not the reviewed identifier value. Audit metadata records only the case ID, research mode and seed kind.

## Provenance and retention

The retained case already stores the normalized research seed. The added `seed_provenance` record stores only the existing reviewed-upload source and `artifact://` locator. That locator carries artifact/candidate identity and mechanically derived page/character position when available; document bytes and extracted surrounding text are not copied into the case.

Quick cases use a bounded report-extension mechanism in `CaseStore.create()`. Extensions may add fields but cannot replace canonical quick-report keys. This keeps provenance attachment single-write and prevents the execution service from reconstructing the canonical quick-report schema itself.

## Fail-closed behavior

- expired or mismatched candidate → not found;
- pending/rejected/reopened or otherwise unauthorized candidate → conflict;
- blocked purpose or missing required consent acknowledgement → rejected before provider execution;
- unsupported candidate kinds remain non-executable through the existing promotion contract;
- review confirmation and promotion still never trigger provider traffic.

## Consequences

Positive:

- reviewed-document authorization remains server-owned at the final pre-execution boundary;
- provider traffic requires an explicit action separate from review state changes;
- retained cases can explain that the seed came from reviewed document evidence;
- no new provider, service, credential or paid dependency is introduced.

Cost:

- the private API gains one more explicit action rather than overloading the generic case endpoint;
- retained case reports gain a small provenance record for reviewed-document seeds.

## Next gate

Expose the review/run workflow and existing source-state/evaluation summaries in the private operator UI, then perform the final V2-D consistency review before activating any new third-party source.
