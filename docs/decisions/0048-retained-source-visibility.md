# ADR 0048 — Retained cases carry one typed source visibility projection

Status: accepted for V2-D closure

## Context

Typed source-run records already describe whether a source executed, returned no match, was unavailable, was blocked, or stopped at a local budget. Converged node payloads retained the source-run projection, but ordinary retained quick cases dropped it. Deterministic source-evaluation counters also existed as a separate helper rather than as part of the retained operator projection.

That split made source visibility depend on report mode and encouraged consumers to reconstruct outcome semantics themselves.

## Decision

`build_source_run_report()` is the single retained source-visibility projection. It now includes the existing deterministic evaluation counters derived from the same ordered `SourceRunRecord` sequence.

Quick retained cases persist this projection under `report.source_runs`. Converged node payloads already use the same helper, so they receive the same evaluation section without a second serialization path.

The projection remains metadata-only. It does not retain identifier values, source locators, provider payloads, credentials, exception text, or timing data. Canonical observations and lead/provenance records keep ownership of those details.

## Consequences

- quick and converged retained reports expose the same typed source-state/evaluation vocabulary;
- the private operator UI can display source status without parsing warnings or rebuilding evaluation rules in browser code;
- source evaluation remains deterministic descriptive counting, not a reliability probability or identity-quality score;
- historical retained cases created before this change may not contain `source_runs` and must remain readable as historical data rather than being backfilled with guessed state.

## Non-changes

This decision does not add a provider, network call, credential, paid dependency, retention duration, recursion capacity, or identity-probability claim.
