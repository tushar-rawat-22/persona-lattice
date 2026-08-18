# ADR 0046 — Private UI resolves canonical retained references

Status: accepted for V2-D closure

## Context

PRs #77 and #79 removed duplicated provenance and connected-field values from new retained reports. Canonical node/quick observations became the retained owners, while admitted edges and quick connected fields kept only references.

The private admin UI still expected the older self-contained display shape. `CaseStore` therefore rebuilt copied `source`, `source_locator` and connected-field values on every API response. That kept the database minimal, but left two representations of the same new report contract in active code and made the API response differ from the retained payload.

Historical retained cases are different: cases created before ADRs 0044 and 0045 already contain self-contained edge or connected-field fields. They must remain readable without rewriting retained data.

## Decision

The private admin UI now resolves new retained references directly.

For quick connected fields it validates:

- the entry is either a legacy self-contained shape or a canonical reference, never both;
- `observation_index` is a valid canonical quick-observation index;
- `kind` maps to the expected reviewed `detail_field`;
- the referenced observation contains non-empty source provenance and the referenced value.

For converged edges it validates:

- the edge is either a legacy self-contained shape or a canonical reference, never both;
- `lead_decision_index` resolves to an admitted lead decision;
- parent, child and reason agree between the edge and decision;
- `source_observation_index` resolves inside exactly one parent node;
- the decision's source field exists on that canonical observation;
- canonical source provenance is present.

If a reference cannot be proven, the UI displays an unavailable-reference message instead of inventing provenance or a value.

`CaseStore` now returns the retained report shape unchanged. The temporary server-side hydration helpers for new quick connected fields and converged edges are removed.

Historical cases remain readable because the UI retains a read-only branch for the older self-contained fields. No retained case migration or write-back occurs.

## Consequences

- API responses and retained report JSON now use the same contract for new cases.
- Canonical observations remain the only owner of the values and provider provenance removed by ADRs 0044 and 0045.
- The browser owns display-time reference resolution, but it does not gain authorization, provider-selection, correlation or research-policy authority.
- Malformed reference-shaped reports degrade visibly instead of being silently expanded by the API.
- Historical cases keep their original self-contained fields and remain readable without database migration.

## Unchanged boundaries

This change does not activate a provider, add an API or credential, alter provider execution, increase recursion limits, extend retention, change M5 semantics or add a paid requirement. The zero-spend baseline is unchanged.
