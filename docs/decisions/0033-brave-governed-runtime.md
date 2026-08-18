# ADR 0033 — Optional Brave search uses the governed runtime

Status: accepted for V2-D migration

## Context

After public DNS moved onto `ProviderRuntime`, the optional Brave exact-match web search was the only remaining network path owned by `legacy_research`. The source already existed in private V1, used `BRAVE_SEARCH_API_KEY`, searched an exact quoted identifier, returned at most ten web results and did not fetch result pages.

Brave's current Web Search documentation still requires a subscription token in `X-Subscription-Token`. Its Search plan is metered, with monthly credits, so PersonaLattice cannot treat it as part of the zero-spend baseline.

## Decision

Register `brave_public_web_index` as an optional governed provider and run configured production searches through the process-wide `ProviderRuntime`.

The adapter keeps the existing behavior:

- only username, email, phone and URL seeds are accepted;
- the query remains an exact quoted identifier;
- Safe Search remains moderate;
- only web results are requested;
- at most ten results are admitted;
- raw responses are capped at 256 KiB;
- the local application budget remains 10 requests per 60 seconds;
- concurrency remains one and the timeout remains five seconds;
- result URLs must pass the existing public HTTP(S) canonicalization rules;
- snippets remain discovery evidence with `identity_claim=false` and `content_fetched=false`;
- result pages are not fetched and snippets do not emit recursive leads.

Quick research passes the actual typed seed kind and caller purpose/consent context into `ProviderRuntime`. Injected `public_search_lookup` callables remain test compatibility only. The older one-argument search helper keeps username/public-research defaults solely for compatibility; new typed callers must use the runtime with their real execution context.

Source-run accounting follows the shared phase-proven outcome contract. Typed policy, configuration, budget, remote-rate, execution and malformed-result failures are recorded only when their execution phase is known. A phase-ambiguous validation failure produces a warning but no source-run record rather than being guessed into an attempted provider failure.

## Zero-spend behavior

No Brave key means no Brave execution attempt. Quick research records the existing optional-not-configured source state and continues with the remaining local and zero-direct-cost sources. A Brave subscription is never required for baseline operation.

The source catalog remains `OPTIONAL`, `METERED` and `METERED_API_KEY`; moving execution behind `ProviderRuntime` does not change those planning facts.

## Consequences

The current network-source migration debt is now zero: every executable network source is owned by `ProviderRuntime`, and the legacy network allowlist is empty.

Brave remains a paid/metered extension. Future pricing, terms or quota changes must be rechecked before any product decision that relies on it. Provider migration is not permission to expand query scope or make the source mandatory.

## Next gate

Finish document-candidate-to-reviewed-lead plumbing and operator source-state/evaluation exposure, then run the final V2-D architecture consistency review before activating any new third-party provider.
