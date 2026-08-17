# ADR 0016 — GitHub public profile lookup uses the governed runtime

Status: accepted for V2-D migration

## Context

After Sherlock moved onto `ProviderRuntime`, GitHub remained a direct HTTP branch
inside `research.py`. The direct path already bounded the public endpoint, timeout
and response size, but it carried a local 20-per-minute budget that did not match
GitHub's unauthenticated primary REST limit of 60 requests per hour. Keeping that
budget while moving the source would have preserved both the architectural split
and an upstream-rate assumption that was too aggressive.

GitHub's official REST API exposes a public `GET /users/{username}` resource. The
public representation may be requested without authentication, returns 404 when
the user does not exist, and includes public profile fields such as login, public
URL, name/company/location/email when the user has made those fields public.

## Decision

Introduce `GitHubPublicProfileProvider` and register it as a reviewed development
provider backed by the shared M3 `ProviderRuntime`.

The provider descriptor uses a local budget of **50 requests per 3600 seconds**.
That leaves headroom below GitHub's documented unauthenticated primary limit
instead of trying to consume the entire upstream allowance.

The adapter:

- accepts only the normalized username seed;
- sends no GitHub credential/token;
- calls only `https://api.github.com/users/{username}`;
- sends the reviewed REST version header used by this repository;
- maps 404 to a valid empty provider result;
- recognizes GitHub rate-limit responses separately;
- treats transient network/server failures as provider failures, not negative
  identity evidence;
- bounds the raw response before JSON parsing;
- requires the returned login to match the requested username under GitHub's
  case-insensitive account-name semantics;
- requires the returned source locator to be an HTTPS `github.com/<login>` public
  profile URL;
- copies only an explicit allowlist of public profile fields;
- excludes private/account-management fields even if an unexpected response ever
  contained them;
- marks the result `account_candidate=true` and `identity_claim=false`.

`ProviderRuntime` adds the shared purpose/consent/status policy, concurrency,
rate, timeout, response-contract/size and source-locator controls around the
adapter.

## No coverage expansion

This migration uses the same public GitHub profile source that private V1 already
used. It does not add repository scraping, commit-email harvesting, organization
membership inference, private-repository access, authenticated GitHub tokens or
additional endpoints.

The source capability remains `github_public_api`; only its runtime owner changes
from frozen `legacy_research` to `m3_governed_adapter`.

## Test injection compatibility

Existing quick-research tests can still provide an injected `github_lookup`
function. That path is test/compatibility glue and retains the same reviewed field
allowlist. Production quick research leaves the injection unset and therefore
uses the governed provider/runtime path.

## Consequences

Positive:

- the frozen legacy network set shrinks by one source;
- GitHub now shares the same provider policy/reliability boundary as Sherlock;
- GitHub response validation happens before profile data becomes a QuickObservation;
- private/account-management response fields cannot leak through generic payload
  copying;
- the local request budget is aligned with anonymous upstream semantics;
- the migration pattern is now proven for an ordinary public REST API, not only a
  subprocess-backed provider.

Costs:

- the provider registry contains another active development descriptor;
- GitHub error handling moves into an adapter that must remain aligned with
  official API semantics;
- direct raw-payload compatibility remains temporarily available for tests until
  legacy quick-research injection surfaces are cleaned up.

## Regression guard

The provider-registry tests assert that GitHub is one of the governed recursive
providers and that its local budget remains 50 requests per 3600 seconds and below
the documented anonymous hourly primary limit. This specifically guards against
reintroducing the stale 20-per-minute setting.

## Next migration

Move GitLab public profile and exact-public-email lookup behind the same runtime
pattern, preserving its current public-only semantics. Codeforces should follow,
then DNS and optional Brave. No new V2 source should be activated until at least
the public-profile legacy set is fully governed.
