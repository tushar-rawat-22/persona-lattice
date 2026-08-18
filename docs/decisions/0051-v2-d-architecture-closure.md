# ADR 0051 — V2-D architecture closure

Status: accepted

## Context

V2-D was intended to make source activation a governed, bounded operation rather
than another branch in the research loop. The final closure audit reviewed the
source catalog/binding/provider/runtime chain, retained evidence ownership,
document-review authority, typed source-state accounting, zero-spend operation,
historical compatibility and documentation consistency.

The audit did find two material gaps before closure. The repository-root deployment
contract still presented a paid Render topology as the default despite the newer
zero-spend rule, and development-status providers were not checked symmetrically
against governed runtime ownership. PR #89 repaired both issues and added ADR
numbering consistency to CI.

## Decision

Close V2-D at the PR #89 implementation checkpoint, subject to its green full CI
run.

The closed architecture has these properties:

- every current executable network source is owned by `ProviderRuntime`;
- the executable legacy-network allowance is empty;
- current development-status providers, governed bindings and process runtime
  membership agree exactly;
- required active recursive sources are zero-spend eligible; metered Brave remains
  optional and is not attempted without configuration;
- local one-admin operation is the default zero-spend deployment authority;
- complete provider evidence/provenance has canonical retained ownership and
  derived report structures use validated references where duplication is not
  justified;
- upload extraction is not research authority: candidates require explicit human
  confirmation and a separate explicit run action before provider execution;
- source-run state distinguishes no-match, unavailable, blocked and budget-stopped
  outcomes using phase-proven attempt semantics rather than warning inference;
- historical retained formats are supported only through explicit read-only
  compatibility paths;
- production recursion remains depth 2 / 12 nodes;
- ADR numbering is unique and contiguous under CI.

## What closure does not authorize

V2-D closure does not activate any planned third-party provider, raise recursion
limits, enable paid dependencies, change M5 into identity probability, widen
retention, weaken authentication, or authorize private-account bypass, credential
collection, hidden government-ID/KYC acquisition, covert device/IP discovery,
live tracking or regulated eligibility decisions.

## Next phase

New source activation is a later phase. Before any candidate source becomes
executable, re-review its current official documentation, terms, quotas, cost,
authentication model, returned fields, contact risk and retention implications.
Prefer zero-cost official/public standards and keep the product functional when
optional integrations are absent.

M10 evaluation remains the gate for increasing recursion or changing correlation
thresholds.
