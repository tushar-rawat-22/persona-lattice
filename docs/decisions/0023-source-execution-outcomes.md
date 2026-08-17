# ADR 0023 — Source execution outcomes are explicit

Status: accepted for V2-D integration

## Context

PersonaLattice now has a typed source-state vocabulary and a deterministic report projection, but quick research still needs a safe way to translate actual execution facts into those records.

The main ambiguity is `unavailable`. A provider can be unavailable after a real execution attempt, an optional source can be unconfigured and never attempted, or a local application budget can stop work before provider contact. Treating all three as the same event would make operator reports misleading and would corrupt later reliability measurements.

## Decision

Add a small outcome-mapping layer with explicit constructors for four cases:

- completed source execution with observations;
- completed source execution with no observations;
- attempted execution that failed, including a distinct remote-rate-limit reason;
- work that did not reach provider execution because the optional source is unconfigured or a local budget stopped it.

The mapping is intentionally based on facts known by the caller, not guessed from warning strings or generic exception text.

A zero-observation completed call is `not_found`, not `unavailable`. A local budget stop and an unconfigured optional source both keep `execution_attempted=false`. A remote rate limit or post-entry execution failure keeps `execution_attempted=true`.

## Boundary

This layer does not inspect provider payloads, copy identifier values, retain exception text, or infer identity. It does not activate a source and it does not change request budgets.

Callers must not label a policy, credential or configuration failure as `execution_failure` unless execution was actually entered. The quick-research integration must preserve that distinction when it wires these records into reports.

## Consequences

The next integration can populate source-state records without duplicating outcome logic across GitHub, GitLab, Codeforces, DNS and optional public search. Evaluation code will also be able to distinguish provider reliability from local policy/budget decisions.

No paid source becomes part of the zero-spend baseline through this change.
