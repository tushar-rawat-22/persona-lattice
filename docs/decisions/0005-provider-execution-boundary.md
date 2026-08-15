# ADR 0005 — provider execution boundary

**Status:** accepted for M3

PersonaLattice now has enough evidence and upload structure to define provider
execution, but it is too early to treat every planned integration as executable.

## Decision

M3 separates three concerns:

1. provider metadata describes source category, review state, contact risk,
   allowed purposes, auth mode and resource budgets;
2. a central authorization function checks purpose, consent, provider review
   state, contact risk and M2 candidate confirmation immediately before a call;
3. `ProviderExecutor` owns rate budget, concurrency, timeout, retry, response-size
   and evidence-persistence behavior.

The first executable adapter is `synthetic_echo`. It has no network access and
exists to make the execution contract testable before any real API is wired in.

Planned phone, username and caller-ID sources remain non-executable until their
status is explicitly promoted after terms/privacy/contact-risk review. Merely
listing a source in the registry is not authorization to call it.

## Retry rule

Only explicitly retryable provider failures (transient failures, remote rate
limits and timeouts) may retry. Validation, policy, missing credentials, local
rate-budget exhaustion and oversized responses fail immediately. Retry count and
delay are bounded by provider metadata.

## Secret boundary

A provider request contains no credential field. Credentials are resolved from
server-side configuration using the descriptor's environment-variable name and
are passed only to the adapter call. Missing credentials fail before adapter
execution.

## Evidence boundary

Provider output is stored as an M1 `PROVIDER` observation with provider name,
version, source category, source locator and retrieval timestamp. Provider output
never becomes a claim automatically.

Document-derived queries carry their M2 candidate provenance. The candidate must
already be human-confirmed and authorized, and its kind/value must match the
stored identifier before an adapter can run.

## Deferred

M3 does not enable:

- real external provider calls;
- public web crawling or arbitrary URL fetching;
- username/social discovery;
- OTP/SMS/call/recovery actions;
- multi-tenant secret storage;
- production billing or background queues.
