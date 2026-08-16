# ADR 0014 — Extract the governed provider runtime before source migration

Status: accepted for V2-D infrastructure

## Context

ADR 0013 made runtime ownership explicit and froze the legacy network boundary.
The next architecture question is how to move those network sources out of
`research.py` without creating another execution framework.

M3 already has the required controls in `ProviderExecutor`, but they are mixed
with evidence-store validation and persistence. Ephemeral/private convergence
needs the same network policy and reliability controls without necessarily
persisting each intermediate provider result to the long-lived M1 store.

Copying the retry/rate/secret/timeout code into a second "research executor" would
create two subtly different security boundaries.

## Decision

Extract the storage-independent part of M3 into `ProviderRuntime`.

`ProviderRuntime` owns:

- provider adapter uniqueness/selection;
- execution-policy authorization;
- server-side credential resolution;
- per-provider local rate budgets;
- per-provider concurrency ceilings;
- bounded retries/backoff;
- per-call timeouts;
- result-contract validation;
- response-size ceilings;
- non-empty source-locator validation.

It returns a `ProviderResult`. It does not persist an Observation.

`ProviderExecutor` remains the persistent M3 facade and owns:

- stored subject existence;
- stored identifier existence/ownership;
- exact stored identifier-kind compatibility;
- confirmed document-candidate alignment with the stored identifier;
- conversion of validated provider output into provenance-bearing M1
  observations.

The executor delegates the runtime work to `ProviderRuntime`.

## Policy ordering

The old `ProviderExecutor` authorized execution before subject/identifier lookup.
That ordering is preserved.

`ProviderRuntime.prepare()` performs the initial policy check and returns the
selected adapter/descriptor without reading credentials or performing network
I/O. `ProviderExecutor` can then validate storage relationships and build the
canonical query.

`execute_prepared()` **re-runs** execution policy immediately before credentials
or network I/O. This redundancy is intentional: the prepared object is ordinary
data, not an unforgeable security token. Manually constructing it must not bypass
purpose/consent/provider-status/contact-risk policy.

## Query binding

A prepared execution can only execute a query whose subject and identifier IDs
match the authorized request. The runtime also validates supported identifier
kind and non-empty identifier value.

For confirmed document candidates, the query's identifier kind/value must match
the reviewed candidate as well. Store-backed execution additionally checks that
the candidate matches the stored M1 identifier.

This prevents a caller from authorizing one reviewed clue and substituting a
different remote query after preparation.

## No behavior expansion

This refactor does not activate a new provider and does not change the source
catalog. Existing `ProviderExecutor` tests remain the primary regression contract
for persistence, retries, rate limiting, timeouts, response limits and
concurrency.

New runtime tests prove the same controls can operate without an EvidenceStore.
That is the prerequisite for migrating ephemeral quick research onto one governed
runtime.

## Next step

After this refactor is green:

1. move Sherlock quick research onto a shared `ProviderRuntime` instance while
   preserving its cross-request rate/concurrency budget;
2. migrate GitHub public profile lookup behind an M3 adapter/runtime contract;
3. repeat for GitLab and Codeforces;
4. then migrate DNS and optional Brave;
5. only after the legacy network set is shrinking predictably, activate the first
   new V2 source.

## Consequences

Positive:

- one implementation owns provider policy/retry/rate/secret/timeout/size rules;
- persistent and ephemeral research can share the same runtime semantics;
- legacy source migration no longer requires copying executor logic;
- future source adapters enter through the M3 boundary rather than `research.py`;
- policy remains fail-closed at the final pre-network gate.

Costs:

- `ProviderExecutor` becomes a facade over another object;
- policy authorization is performed twice in the prepared store-backed path;
- migration still requires source-specific adapters and fixture tests.

Those are acceptable costs. Duplicating a provider-security boundary would be a
much larger long-term risk.
