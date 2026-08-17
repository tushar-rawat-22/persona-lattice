# ADR 0030 — Provider outcomes require a provable execution phase

Status: accepted for V2-D architecture closure

## Context

PersonaLattice now retains typed source-run states for policy blocks, missing server-side configuration, execution failures, remote rate limits, malformed results and local budget stops. Those states are useful only if their attempt semantics are true.

`ProviderValidationError` was too broad for that job. The runtime can raise it before a provider call for request/provider mismatches, but it was also used after a provider returned malformed output. A caller seeing only that exception type could not honestly say whether external execution happened.

## Decision

Keep `ProviderValidationError` as the phase-ambiguous validation class and add `ProviderResultValidationError` for validation failures that are known to occur after provider output has returned.

The runtime now uses the post-attempt type for:

- an invalid `ProviderResult` contract;
- a provider payload that cannot be serialized into the bounded result contract;
- an observation with a blank source locator.

Response-size violations remain `ProviderResponseTooLarge`; they are already provably post-attempt. Policy rejection and missing API-key configuration keep their existing dedicated exception types and remain pre-attempt outcomes.

A shared `source_provider_exception_record()` mapper converts only these provable exception classes into source-run records. Generic `ProviderValidationError` deliberately maps to no source-run record because its phase is not encoded.

## Consequences

Source evaluation can distinguish:

- policy rejection: no provider attempt;
- missing required server-side secret: no provider attempt;
- local rate budget stop: no provider attempt;
- malformed returned result: provider attempt occurred;
- remote rate limit, timeout, transient failure and oversized response: provider attempt occurred;
- generic validation failure: unknown phase, therefore unclassified.

This avoids inflating provider-failure counts with local validation defects and avoids hiding malformed remote output as a generic local error.

## Boundary

This change does not activate a provider, add credentials, change recursion limits, alter source coverage or change M5 semantics. It only makes an existing execution boundary more explicit.

The next step is to replace quick research's local exception mapping with the shared phase-proven mapper, retaining the special injected-test compatibility path separately.
