# ADR 0032 — Quick research uses the shared source-outcome mapper

Status: accepted for V2-D architecture closure

## Context

`ProviderRuntime` now distinguishes failures whose execution phase is known from generic validation failures whose phase is ambiguous. The source-reporting layer also has one `source_provider_exception_record()` function that maps those typed exceptions into `SourceRunRecord` states.

Quick research still kept a second exception classifier in `research.py`. It covered local budgets, remote rate limits and a subset of execution failures, but it did not understand provider-policy rejection, missing server-side configuration or post-attempt malformed results. Leaving both classifiers in place meant the same runtime failure could be reported differently depending on which path consumed it.

## Decision

Quick research delegates provider exceptions to `source_provider_exception_record()`.

The shared mapper therefore remains authoritative for:

- local pre-call rate-budget stops;
- provider-policy rejection before execution;
- required server-side configuration missing before execution;
- malformed provider output after a proven attempt;
- remote rate limits;
- timeout, transient, oversized-response and proven execution failures;
- phase-ambiguous `ProviderValidationError`, which remains unclassified.

Injected compatibility lookups are the one explicit exception. They execute outside `ProviderRuntime`; if such a callable raises an otherwise-unclassified exception, quick research may record a generic execution failure because invocation of that callable is itself the proven attempt boundary. Typed pre-call outcomes still keep their shared semantics.

## Consequences

There is now one provider-exception-to-source-state vocabulary for governed execution. Adding or correcting a phase-proven runtime outcome no longer requires a second classification table in quick research.

Warnings remain human-readable operational context. They are not parsed to derive source states, and exception text is not copied into retained source-run records.

This change does not activate a provider, alter source coverage, raise recursion limits, add credentials or make an optional metered source part of the zero-spend baseline.

## Next gate

Migrate the already-existing optional Brave exact-match search behind `ProviderRuntime` without making it mandatory. Once that path is governed, remove the final `legacy_research` network allowance before any new third-party provider is activated.
