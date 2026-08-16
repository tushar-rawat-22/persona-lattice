# ADR 0015 — Quick Sherlock uses the shared governed provider runtime

Status: accepted for V2-D migration

## Context

ADR 0014 extracted `ProviderRuntime` from the persistent M3 executor. Before that
refactor, quick username research used Sherlock through a smaller hand-built path:

- call `authorize_execution()` directly;
- consume a standalone Sherlock `RateBudget`;
- invoke the adapter directly.

That path had the same 6-per-60-second rate ceiling as the Sherlock descriptor but
it did not automatically inherit the runtime's provider concurrency, timeout,
response-size and source-locator validation.

Keeping both implementations would defeat the purpose of the runtime extraction.

## Decision

Quick username research now executes Sherlock through `ProviderRuntime`.

Production uses one module-level Sherlock adapter and one module-level runtime.
That preserves the existing cross-request provider rate/concurrency budget rather
than constructing a fresh budget for every research call.

Tests may inject a provider instance. An injected provider receives its own runtime
for deterministic isolation, but it must still satisfy the same descriptor,
policy, timeout, response-size and source-locator contracts.

## Unchanged enrichment path

GitHub, GitLab, Codeforces and optional public-web search remain on their existing
private-V1 paths in this block. They are already marked as frozen legacy migration
debt by ADR 0013 and will move one at a time.

This block intentionally changes only Sherlock so failures are attributable and
the migration pattern can be validated before touching the other working sources.

## Security effect

This is a tightening/refactor, not a coverage expansion.

The runtime now enforces for quick Sherlock:

- purpose/consent/provider-status policy;
- request/query subject and identifier binding;
- provider-supported identifier kind;
- provider concurrency ceiling;
- 6-per-60-second local rate budget from the descriptor;
- 8-second timeout;
- 64 KiB result ceiling;
- valid `ProviderResult` contract;
- non-empty source locator.

No new site, provider or Sherlock option is enabled.

## Consequences

Positive:

- quick and persistent provider execution now share the same M3 runtime controls;
- the standalone Sherlock rate-budget duplicate is removed;
- malformed provider output fails before it becomes a QuickObservation;
- source migration has a proven incremental pattern.

Costs:

- injected test providers are subject to stricter runtime output validation;
- username research now depends directly on the shared runtime module;
- the remaining GitHub/GitLab/Codeforces/DNS/Brave legacy paths are more visible
  as the next migration debt.

## Next migration

Move GitHub public-profile lookup behind an M3 descriptor/adapter plus
`ProviderRuntime` while preserving:

- public-profile fields only;
- no authentication requirement unless a future reviewed mode explicitly needs
  it;
- current timeout/response-size ceiling;
- 20-per-60-second local rate budget or a more conservative reviewed equivalent;
- 404 as not-found, not an error;
- account-candidate semantics, never identity proof.
