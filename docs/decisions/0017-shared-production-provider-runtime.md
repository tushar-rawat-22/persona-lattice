# ADR 0017 — Quick research uses one process-wide governed provider runtime

Status: accepted for V2-D runtime consolidation

## Context

Sherlock and GitHub were already migrated from direct/private-V1 execution onto the M3 `ProviderRuntime`, but `research.py` still instantiated a separate module-level runtime for each production provider.

That arrangement was functionally correct for two providers, yet it created the wrong scaling shape for V2-D. Every later migration could add another runtime singleton and another place that implicitly owned rate/concurrency state. The provider runtime is supposed to be the execution boundary; production ownership should therefore be explicit and centralized before GitLab, Codeforces, DNS or optional Brave move behind it.

## Decision

Create one process-wide `DEFAULT_PROVIDER_RUNTIME` for production quick research and register the current governed quick-research adapters in it.

Today that set is intentionally limited to:

- `sherlock`
- `github_public_api`

The exact adapter instances owned by that runtime are also exported as `DEFAULT_SHERLOCK_PROVIDER` and `DEFAULT_GITHUB_PROVIDER` so compatibility code can reference the same instances without constructing fresh budgets.

`research.py` now uses that shared runtime for both normal Sherlock execution and GitHub enrichment. An explicitly injected Sherlock provider still receives an isolated runtime for tests/compatibility, because injected adapters must not mutate or consume production budgets.

## Invariants

This consolidation does not change source coverage or provider policy.

- no new external source or endpoint is activated;
- provider descriptors remain the policy source of truth;
- each production provider keeps its existing timeout, response-size, concurrency and rate limits;
- purpose/consent checks still execute inside `ProviderRuntime`;
- no credentials are added;
- recursive depth/node limits and M5 identity semantics are unchanged;
- legacy GitLab, Codeforces, DNS and optional Brave execution remains legacy debt until separately migrated and reviewed.

## Consequences

Positive:

- production rate/concurrency ownership has one explicit process boundary;
- later provider migrations add adapters to one runtime instead of creating additional runtime globals;
- tests can assert that runtime membership and provider registry descriptors stay aligned;
- accidental adapter re-instantiation is easier to detect.

Cost:

- the shared runtime module becomes infrastructure that must remain intentionally small and reviewed;
- tests that previously patched provider-specific runtime globals must patch the shared runtime reference instead.

## Next migration

Move GitLab public profile and exact-public-email lookup behind the governed provider adapter/runtime boundary as a separate PR. Do not combine that behavioral migration with this ownership refactor.
