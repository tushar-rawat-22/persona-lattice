# ADR 0054 — Public-web withholding is an attempted neutral source outcome

Status: accepted for Bluesky adapter pre-activation

## Context

The Bluesky admission preflight established two source results that are neither a
normal miss nor a provider reliability failure:

- a returned profile carrying `!no-unauthenticated`;
- an account that the AppView reports as suspended or deactivated.

Both outcomes happen after source contact. Treating either as `not_found` would
misstate what the source returned. Treating either as `unavailable` would inflate
provider-failure counters even though the provider answered successfully.

Official Bluesky/AT Protocol material was rechecked on 2026-08-19. Public
`app.bsky.*` reads may use `https://public.api.bsky.app` without authentication;
the cached public AppView is recommended for public-web clients. The handle
specification still requires DNS-hostname-shaped handles, and Bluesky still
defines `!no-unauthenticated` as inaccessible to logged-out clients that respect
the label. The current AppView implementation also distinguishes profile absence
from account takedown/deactivation.

## Decision

Add a typed `withheld` source state with two reasons:

- `public_web_opt_out`;
- `account_unavailable`.

A withheld result proves an execution attempt completed, but it is not counted as
a failed attempt. Source evaluation reports it separately from result-bearing,
not-found and failed source runs.

Add the bounded Bluesky public-profile adapter now, but keep its provider
descriptor and source capability in `PLANNED` state. This block does not add a
source binding, shared-runtime owner or quick-research call. Atomic activation is
a separate gate after this adapter/outcome contract passes the full repository CI
matrix.

The adapter is limited to the official public AppView `getProfile` route, accepts
no credential, validates a real AT Protocol handle before network execution, and
retains only DID, normalized handle and optional display name plus explicit
account-candidate/non-identity flags. Description, avatar, counts, viewer state and
unexpected fields are not admitted.

A local 30-request-per-minute descriptor budget is an application safety ceiling,
not a statement about Bluesky's upstream quota. Bluesky currently describes its
public AppView limits as generous rather than publishing a fixed per-route quota.

## Consequences

M10 source reliability counters no longer need to misclassify a visibility choice
or account state as provider failure. Future sources may reuse `withheld` only
when execution is provable and the provider returned a neutral non-evidence
outcome; it is not a generic escape hatch for errors.

Bluesky remains non-executable until catalog status, reviewed policy, source
binding, process-wide `ProviderRuntime` ownership and quick-research/source-run
wiring can move together in one reviewed change.

Production recursion remains depth 2 / 12 nodes. M5 remains uncalibrated
evidence-strength triage and not identity probability.
