# ADR 0049 — Private case views consume retained source state directly

Status: accepted for V2-D closure

## Context

The retained case contract already records two operator-relevant facts that the private case view did not show:

- `seed_provenance` for cases started from a reviewed upload candidate;
- typed `source_runs` projections with deterministic source-state and evaluation counters.

Leaving those fields invisible made the operator fall back to warnings and raw observations to understand whether a source ran, returned no match, failed, was locally budget-stopped, or was optional and not configured. Reconstructing those semantics in the browser would create a second policy implementation and would make historical cases ambiguous.

## Decision

The private case view reads the retained contracts directly.

For reviewed-document cases it shows the retained seed-provenance source and locator and whether the seed was human reviewed.

For quick cases it renders the top-level retained `source_runs` projection. For converged cases it renders each node's retained `source_runs` projection. The UI displays the stored state, reason, attempt flag, observation count and deterministic aggregate counters. It does not infer source state from warning text, missing observations or provider names.

Historical cases that predate the typed source-run projection are shown as having source execution state unavailable. The browser does not backfill or guess missing state.

## Boundaries

This change is display-only. It does not:

- call a provider;
- change provider admission, rate or cost policy;
- change recursion limits;
- retain another copy of provider payloads, identifiers, source locators or exception text;
- turn source counters into reliability probabilities;
- change M5 evidence or identity semantics.

The zero-spend baseline is unchanged. Optional metered providers remain optional.

## Consequences

The operator can now distinguish source execution outcomes without reading implementation warnings, and the browser remains a consumer of backend policy rather than another policy authority.

The remaining V2-D work is a final architecture, compatibility, privacy, documentation and zero-spend closure audit. New third-party provider activation remains deferred until that audit is complete.
