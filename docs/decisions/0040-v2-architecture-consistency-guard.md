# ADR 0040 — Cross-layer V2 architecture consistency guard

Status: accepted for V2-D closure

## Context

V2-D now has separate declarations for source capabilities, executable source bindings, provider descriptors and the process-wide production `ProviderRuntime`. Each layer has its own tests, but that is not enough to prove the layers agree with one another.

A future change could add a reviewed governed binding and provider descriptor while forgetting to register the adapter in the shared runtime. The binding tests and the hard-coded runtime-membership test could both remain green even though production execution would have no process-owned adapter for that source.

The zero-spend rule also needs a general invariant rather than a source-specific assertion. A required active source must not silently become metered or otherwise non-zero-spend while still being treated as part of the baseline.

## Decision

Add a cross-layer regression suite derived from the live declarations.

The suite requires that:

- every `M3_GOVERNED_ADAPTER` binding has exactly one provider name;
- governed provider names are unique across current bindings;
- the set of governed binding provider names exactly matches the adapters owned by the process-wide production runtime;
- each runtime-owned adapter uses the exact reviewed provider descriptor registered for that provider;
- runtime-owned sources are current, source-policy reviewed and recursive-eligible;
- every required `ACTIVE` recursive source remains zero-spend eligible;
- any current recursive source that is not zero-spend eligible must remain `OPTIONAL`;
- a planned, deferred or unreviewed source cannot appear in the production runtime without first crossing the catalog and binding admission boundaries.

This stays in the test layer rather than importing intelligence declarations into `providers/shared_runtime.py`. Runtime construction should remain small and dependency-light; CI is the admission gate that prevents cross-layer drift from merging.

## Consequences

The provider/runtime tests no longer rely only on parallel hard-coded expectations. Adding or changing a source now requires catalog, binding, registry and runtime ownership to remain mutually consistent.

The rule does not prohibit optional metered integrations. It prevents them from becoming required baseline sources. Brave can therefore remain an optional governed adapter while the default product continues to have a zero-spend path.

No provider behavior, source coverage, credentials, retention, recursion limits or identity semantics change in this decision.
