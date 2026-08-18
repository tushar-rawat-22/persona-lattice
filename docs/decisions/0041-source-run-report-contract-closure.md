# ADR 0041 — Converged reports require the typed source-run contract

Status: accepted for V2-D architecture closure

## Context

`QuickResearchReport.source_runs` is now the canonical execution-state contract for quick research. It carries typed, privacy-bounded facts such as completed execution, not-found, local budget stop, remote failure and optional-unconfigured state.

Convergence still retained an older compatibility shim that used `getattr(report, "source_runs", ())`. A custom or stale runner could therefore omit the field entirely and still produce an apparently valid converged report with an empty source-state projection.

That behavior hides contract drift. An absent contract is different from a valid contract containing zero records.

## Decision

Converged report projection now reads `QuickResearchReport.source_runs` directly.

A valid quick-research report with no source-run records still produces the explicit empty projection. A runner that no longer satisfies the `QuickResearchReport` contract fails instead of being silently interpreted as having no source execution state.

The source-run projection remains privacy-bounded. It contains source name, lead kind, typed state/reason, observation count and execution/terminal flags; it does not duplicate identifier values, source locators, provider payloads, credentials or exception text.

## Consequences

Positive:

- stale/custom runners cannot silently erase source execution state from retained converged reports;
- an empty source-run set remains distinguishable from a missing report contract;
- source-state evaluation continues to use one typed authority instead of compatibility inference;
- no provider, network call, retention scope or zero-spend dependency changes.

Cost:

- out-of-tree or old test runners that return report-like objects rather than `QuickResearchReport` must adopt the current typed contract.

## Boundaries

This decision does not change provider execution, graph limits, source activation, M5 semantics, retained observation payloads or the public/private product boundary. Production recursion remains depth 2 / 12 nodes.
