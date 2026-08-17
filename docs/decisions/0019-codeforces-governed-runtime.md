# ADR 0019 — Codeforces public profile lookup uses the governed runtime

Status: accepted for V2-D migration

## Context

After GitHub and GitLab moved onto the shared process-wide `ProviderRuntime`, Codeforces remained a direct network branch in `public_profiles.py` and `research.py`.

The existing source uses Codeforces' anonymous `user.info` API method with one handle and `checkHistoricHandles=true`. The official API documentation states that anonymous methods expose public data, that `user.info` returns User objects for requested handles, and that the API may be called at most once every two seconds.

The legacy PersonaLattice helper used a 20-requests-per-minute sliding budget. Although that average is below 30 requests/minute, it does not encode Codeforces' actual minimum spacing rule and can permit short bursts that violate the upstream contract.

## Decision

Introduce `CodeforcesPublicProfileProvider`, register it as a reviewed development provider, and execute production Codeforces enrichment through the shared `ProviderRuntime`.

The adapter:

- accepts only normalized username seeds;
- sends no credential or API key;
- calls only the anonymous `https://codeforces.com/api/user.info` method;
- preserves `checkHistoricHandles=true` from the existing source behavior;
- bounds the raw response before JSON parsing;
- distinguishes not-found, upstream call-limit, transient, execution and validation failures;
- admits only the previously reviewed public User-field allowlist;
- generates the source locator only on the fixed `https://codeforces.com/profile/<handle>` origin;
- marks every result `account_candidate=true` and `identity_claim=false`;
- labels exact returned handles as `matched_by=exact_handle` and renamed-account results as `matched_by=historic_handle`.

The provider descriptor sets `rate_limit=1`, `rate_window_seconds=2.0`, and `max_concurrency=1`. This deliberately corrects the legacy 20/minute approximation to match the documented upstream request interval.

## No coverage expansion

This migration does not add any Codeforces method, submission/source-code lookup, friends lookup, authentication, API key, contest-private data, account takeover surface, or additional recursive lead class.

It retains only the public profile source already used by private V1. Historic-handle resolution remains account-candidate evidence rather than proof that two real-world identities are the same person.

The old `lookup_codeforces_handle` name remains as compatibility glue for injected tests/callers, but delegates to the new adapter fetcher. Production quick research recognizes the default helper and uses the governed shared runtime instead.

## Consequences

Positive:

- Codeforces no longer owns an independent production network/rate boundary;
- the shared runtime now owns Sherlock, GitHub, GitLab and Codeforces policy state;
- the upstream request-spacing rule is encoded exactly rather than approximately;
- Codeforces `FAILED` call-limit responses become typed provider rate-limit failures;
- unexpected response fields cannot enter observations through generic payload copying;
- legacy recursive network debt shrinks to public DNS and optional Brave search.

Costs:

- Codeforces calls can now fail closed under the stricter one-per-two-seconds local budget rather than being burstable;
- historic-handle matches require downstream consumers to preserve the `matched_by` distinction;
- the compatibility helper remains temporarily available until legacy injection seams are removed.

## Next migration

Move public DNS infrastructure lookup behind an appropriate governed network-runtime boundary without turning hostname infrastructure addresses into person/device IP leads. Optional metered Brave search should remain separate and must not become zero-spend recursive behavior.
