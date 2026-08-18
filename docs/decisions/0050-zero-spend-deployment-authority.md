# ADR 0050 — Zero-spend operation is the default deployment authority

Status: accepted for V2-D closure audit

## Context

The V2 rules require PersonaLattice to remain usable without paid hosting,
databases, proxies, APIs or enrichment. The repository already supported local
operation, but the root-level `render.yaml` still described two paid `starter`
services plus persistent storage and the deployment runbook treated that topology
as the normal production path.

That was an authority conflict. A paid topology can be useful as an optional
reference, but it must not look like the default contract while the product
claims a zero-spend baseline.

## Decision

Make local one-admin operation the default zero-spend operating contract and move
the reviewed Render topology to `deploy/render-paid.yaml` as an explicitly
optional paid reference.

The repository root no longer contains `render.yaml`. CI asserts both that the
root paid Blueprint is absent and that the optional reference retains the
previous private-service, persistent-disk, cookie and proxy-header protections.

`docs/ZERO_SPEND_RUNBOOK.md` is the authoritative baseline runbook. It uses the
operator's existing machine, local SQLite storage, the local API and the local
Next.js application. Brave remains omitted unless its optional metered key is
deliberately configured.

## Consequences

- cloning PersonaLattice does not present a paid hosted topology as the default;
- the private one-admin product remains fully usable without buying hosting or a
  database;
- the previously reviewed Render security topology is preserved for an operator
  who intentionally chooses it;
- hosted zero-cost options are not promised in advance, because provider plans,
  storage limits and terms change;
- any future hosted baseline must be reviewed separately for security, persistence,
  privacy and current cost before it can replace local operation.

## Non-changes

This decision does not change provider execution, research coverage, retained-case
semantics, authentication, recursion limits, M5 behavior or optional third-party
source activation.
