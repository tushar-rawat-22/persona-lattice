# ADR 0030 — Source outcome reporting records only provable execution facts

Status: accepted for V2-D architecture closure

## Context

The source-run contract already distinguishes completed results, no-match results, local budget stops, optional-unconfigured sources, attempted execution failures and remote rate limits. Three operationally different cases were still missing from the stable vocabulary: provider-policy rejection before execution, a required server-side credential missing before execution, and malformed provider output after an execution attempt.

Collapsing those cases into `execution_failure` would corrupt later reliability measurements. A policy rejection or missing credential is not provider contact. Conversely, malformed output is a failed attempt and should count against execution quality.

Generic validation errors remain ambiguous because validation can happen before or after provider execution. They must not be classified by guesswork.

## Decision

Extend `SourceRunReason` with three explicit reasons:

- `provider_policy` — provider execution was blocked by policy before an attempt;
- `credential_not_configured` — a required server-side credential was absent before an attempt;
- `malformed_result` — provider output was received but failed a post-attempt runtime result check.

The state mapping is:

- provider policy -> `blocked`, `execution_attempted=false`;
- credential not configured -> `unavailable`, `execution_attempted=false`;
- malformed result -> `unavailable`, `execution_attempted=true`.

Add dedicated constructors for those records rather than allowing callers to assemble them ad hoc. Extend deterministic source-evaluation counters so the three classes remain separately measurable.

## Boundaries

This decision does not make every `ProviderValidationError` a malformed result. Callers may emit `malformed_result` only when the execution boundary proves provider output was already returned. Preflight validation, policy and configuration failures remain non-attempt states.

No exception text, credential value, identifier value, source locator or provider payload is copied into the source-run record or evaluation counters.

This block adds no provider, network call, credential, paid dependency, recursion capacity or identity-semantic change.

## Consequences

Evaluation can now separate source reliability from local policy/configuration failures without manufacturing attempt counts. The full source-state fixture matrix must cover the new reasons, so future vocabulary changes cannot silently alter measurement semantics.

The next step is to wire these constructors into quick-research/runtime exception handling only where the concrete exception and execution phase prove the correct classification. Ambiguous validation errors should continue to produce no typed record until that phase is explicit.
