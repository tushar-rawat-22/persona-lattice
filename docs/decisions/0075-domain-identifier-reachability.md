# ADR 0075 — DOMAIN uses the canonical M1 identifier path

Status: accepted for the RDAP activation sequence

## Context

The V2 lead graph already represented `DOMAIN`, but quick research and M1 did not. Live M5 converts every converged research node back through M1 identifier normalization, so adding only a `ResearchKind.DOMAIN` value would have created a half-supported path.

The graph also had a small domain canonicalizer of its own. Keeping that beside a future M1 domain normalizer would allow the two layers to drift.

## Decision

Add `DOMAIN` to the M1 identifier vocabulary and give it one conservative normalization rule for explicit public DNS names. The rule canonicalizes IDNs to ASCII A-labels and rejects URLs, IP literals, local-use names, malformed labels and whitespace-bearing values.

`LeadKind.DOMAIN` now delegates to that M1 normalizer. `ResearchKind.DOMAIN` is also executable, so an explicit domain seed can pass through quick research, convergence and the ephemeral M1/M5 graph without a special-case bypass.

This block does not activate RDAP. Until a reviewed domain provider is activated, explicit domain quick research returns a normalized zero-observation report. That makes the seed type structurally reachable without pretending that an external lookup occurred.

## Recursion boundary

Discovered domain fields remain `DISPLAY_ONLY`. Adding an executable explicit DOMAIN seed does not make domains emitted by email or URL observations automatic pivots. Any future change to that disposition requires a separate evaluated policy decision.

## Consequences

Positive:

- quick research, convergence, lead comparison and live M5 use the same domain representation;
- M5 can admit a domain seed into its ephemeral evidence graph without an ad-hoc normalization path;
- RDAP activation can now target an existing executable seed kind instead of changing the identity model in the same provider PR.

Costs and limits:

- RDAP is still planned and no subject-provider request is made by this change;
- existing persistent M1 databases are not silently rewritten; deployments that persist the evidence schema must recreate or deliberately migrate the enum constraint before storing DOMAIN identifiers there;
- discovered domains remain non-recursive.

## Next gate

Finish the RDAP activation sequence only after the provider adapter uses this canonical DOMAIN value, preserves `routing_unavailable` as a pre-provider non-attempt, and passes the existing catalog/binding/runtime/source-state/privacy invariants.
