# ADR 0022 — Source-run state has a privacy-bounded report projection

Status: accepted for V2-D architecture closure

## Context

ADR 0021 introduced a typed source-run state contract, but the contract by itself was not yet a stable report format. Convergence and retained-case reporting need to distinguish source outcomes such as executed, not found, unavailable and budget stopped without creating another store of identifiers, source URLs, provider payloads or exception text.

A report projection also needs deterministic ordering. Source execution is increasingly concurrent, so output order must not depend on task completion order.

## Decision

Add a small `source_reporting` module that serializes `SourceRunRecord` values into a deterministic, privacy-bounded operator projection.

Each record exposes only:

- logical source name;
- lead kind;
- source state and stable reason;
- observation count;
- whether execution was attempted;
- whether the state is terminal for automation.

The aggregate projection adds record, attempted-execution and terminal counts plus sorted state/reason counts. Records are sorted by stable non-sensitive fields before serialization.

The projection deliberately excludes identifier values, source locators, provider payloads, credential/configuration values and exception text. Canonical lead and Observation records remain the owners of identifier/provenance detail.

## Consequences

Positive:

- retained reports can expose source lifecycle state without duplicating personal identifiers;
- concurrent execution cannot make report ordering nondeterministic;
- local budget stops remain distinguishable from remote rate limits and execution failures;
- optional-not-configured remains an explicit no-attempt state;
- an empty source scope is represented explicitly rather than disappearing from the report contract.

Costs:

- this projection does not identify which exact lead value a state belonged to; callers must keep the record inside the existing node/lead context when that relationship matters;
- this block does not yet populate source-run records from every quick-research path or change the retained converged report schema.

## Next step

Wire the projection into node/converged report construction while keeping the current report version additive and backward compatible. Then populate typed source states at the quick-research execution boundary, where attempted/not-found/unavailable semantics are known rather than inferred from observations.
