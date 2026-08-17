# ADR 0018 — GitLab public profile lookup uses the governed runtime

Status: accepted for V2-D migration

## Context

GitLab username and exact-public-email enrichment still executed through the frozen `public_profiles.py` network helper after Sherlock and GitHub had moved onto the shared `ProviderRuntime`. That left purpose policy, concurrency, rate state and provider result validation split across two execution models.

GitLab's current Users API documents `GET /users` filters for an exact `username` and `public_email`. The migration keeps those two existing filters only. It does not add broad search, project enumeration, repository inspection, private membership access or authentication.

## Decision

Introduce `GitLabPublicProfileProvider` and register it as a reviewed development provider owned by the process-wide shared `ProviderRuntime`.

The adapter:

- accepts only normalized username or email identifiers;
- sends no GitLab credential or token;
- calls only the public `https://gitlab.com/api/v4/users` resource with either `username` or `public_email`;
- preserves the previous 4-second request timeout and conservative 20-per-minute local budget;
- bounds raw responses before JSON parsing;
- maps 429 responses to the provider runtime's remote-rate-limit path and treats transient network/server failures separately from negative evidence;
- requires an exact case-insensitive username/public-email match before admitting an observation;
- requires the returned public profile URL to be `https://gitlab.com/<username>` with no query or fragment;
- copies only the previously reviewed public profile field allowlist;
- marks results `account_candidate=true` and `identity_claim=false`;
- records whether the match came from `username` or `exact_public_email`.

Production username and email quick research now use this provider through the shared runtime. Existing injected lookup hooks remain compatibility/test seams and do not own production rate state.

## Policy review

As of 2026-08-17, GitLab documents both `username` and `public_email` filters on the Users API. GitLab.com documents substantially higher general unauthenticated traffic limits than this repository's retained 20-per-minute local budget. We deliberately keep the old lower application budget rather than consuming newly available upstream capacity.

## Consequences

Positive:

- the legacy network set shrinks to Codeforces, public DNS and optional Brave search;
- GitLab shares purpose, status, concurrency, timeout, response-size and rate enforcement with other governed providers;
- exact public-email matching fails closed inside the adapter before observations enter research output;
- production GitLab budgets are process-wide rather than hidden in a legacy helper.

Costs:

- the provider registry now has one descriptor that accepts two identifier kinds;
- compatibility helpers remain temporarily in `public_profiles.py` for injected tests and should be removed when legacy quick-research injection surfaces are retired.

## Next migration

Move Codeforces public-profile lookup behind the shared runtime. Keep DNS and optional Brave separate so each network boundary remains independently reviewable.
