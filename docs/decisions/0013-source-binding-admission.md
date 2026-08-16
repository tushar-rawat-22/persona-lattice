# ADR 0013 — Source capability is not source execution

Status: accepted for V2-D infrastructure

## Context

V2-C introduced a capability catalog and source planner. That solves the planning
problem: PersonaLattice can describe which lead kinds a source accepts/emits,
whether it is current/deferred/planned, whether it needs credentials, and whether
it fits a zero-spend plan.

It does **not** solve the runtime problem.

Private V1 currently has three different implementation shapes:

1. deterministic local logic such as identifier parsing and libphonenumber
   metadata;
2. Sherlock, which already uses the M3 provider descriptor/policy/adapter
   contract;
3. older network lookups embedded directly in `research.py` or helper modules
   (GitHub, GitLab, Codeforces, DNS and optional Brave search).

Adding Bluesky/Gravatar/RDAP/WebFinger directly to the third shape would create a
second provider framework by accident. It would also let source catalog metadata
drift away from what the runtime can actually execute.

## Decision

Add an explicit **source binding admission layer** between source planning and
runtime execution.

Every current recursive source must have exactly one binding that states which
existing execution boundary owns it:

- `local_deterministic` — no external network request;
- `m3_governed_adapter` — a source backed by the existing governed provider
  descriptor/policy/adapter model;
- `legacy_research` — a frozen migration-only path for network sources that
  predate V2-D.

A binding still does not grant permission to execute. It only makes runtime
ownership explicit so the existing live policy can be applied and drift can fail
closed.

## No second executor

PersonaLattice already has a mature M3 `ProviderExecutor` that provides:

- subject/identifier ownership validation;
- purpose/consent policy immediately before execution;
- server-side secret resolution;
- per-provider concurrency and rate budgets;
- retry and timeout handling;
- response-size ceilings;
- provenance-bearing M1 provider observations.

V2 will not create another generic HTTP/provider executor beside it.

Future external source adapters should converge on the M3 execution boundary.
The source catalog and binding layer answer planning/runtime ownership questions;
M3 remains the governed execution mechanism.

## Frozen legacy network boundary

The migration-only set is deliberately exact:

- `github_public_api`
- `gitlab_public_api`
- `codeforces_public_api`
- `public_dns_infrastructure`
- `brave_public_web_index`

No new V2 source may be added to that allowlist as a shortcut.

The DNS source is explicitly classified as legacy network I/O rather than
"local". Resolving a public hostname is bounded infrastructure metadata, but it
still performs network work and should not be mislabeled as deterministic local
execution.

The intended migration is to shrink this legacy set to zero.

## Capability is broader than current wiring

A source capability describes what the source family can support under reviewed
semantics. A binding describes what PersonaLattice has actually wired today.

Therefore the binding's accepted lead kinds must be a **non-empty subset** of the
capability declaration, not necessarily equal to it.

This distinction caught a real overclaim during review: the DNS capability can
work from a domain, but the current private-V1 research runner has no `DOMAIN`
research seed and only invokes DNS after a URL seed. The binding therefore admits
`URL` today and leaves `DOMAIN` visibly deferred. The source planner must not call
that current coverage until the domain runtime path actually exists.

This is the desired failure mode: broad source potential never masquerades as
implemented product coverage.

## M3 binding invariants

An M3-bound source must:

- exist in the provider registry;
- be in the reviewed development/executable status used by the current runtime;
- have `ContactRisk.NONE_KNOWN` for silent recursive research;
- declare at least one allowed purpose;
- declare identifier kinds that exactly match the **current binding**.

Currently Sherlock is the only source in this class. Its quick-research path
already uses the M3 descriptor, `authorize_execution()` and adapter contract, but
still invokes the adapter directly. Final unification should route even this path
through `ProviderExecutor` so one mechanism owns all external provider execution.

## Capability/binding invariants

A current binding must point to a source capability that is:

- `active` or `optional`;
- source-policy reviewed;
- recursive-eligible.

Every bound lead kind must be declared by that source capability. Conversely,
every current recursive source must have one runtime owner. Import/test-time
validation compares source-name sets exactly, while per-kind planning checks
whether the current binding actually wires the requested kind.

Adding an `active` source without runtime ownership therefore fails. Adding a
broader capability kind without runtime wiring appears as deferred coverage rather
than becoming executable by implication.

Planned, review-required, manual-only and reference-only sources have no
executable binding.

## Source planner consequence

`build_source_plan()` validates both runtime ownership and the requested lead kind
before reporting an active or optional source as current coverage. A capability
that exists but is not wired for that lead kind is placed in `deferred`.

This is still non-executing. It means only:

> policy-reviewed capability metadata and an explicit runtime path both exist for
> this lead kind.

Purpose/consent/credentials/rate/resource gates still run at execution time.

## Next migration

Before activating a new public API, migrate the existing network sources behind a
single governed runtime contract, starting with one low-risk public profile
adapter.

Recommended order:

1. GitHub public profile;
2. GitLab public profile/exact public email;
3. Codeforces public profile;
4. public DNS infrastructure;
5. optional Brave exact-public-web search;
6. Sherlock final execution-path unification through `ProviderExecutor`.

Only after that migration pattern is proven should V2 activate Bluesky, Gravatar,
WebFinger/ActivityPub or RDAP.

## Consequences

Positive:

- new APIs cannot expand the old hard-coded research branch by accident;
- source catalog/runtime drift becomes a startup/CI-visible failure or deferred
  coverage state;
- the project reuses M3 security/reliability controls instead of duplicating them;
- network-vs-local execution is represented honestly;
- source capability breadth cannot overstate current product coverage;
- migration debt is a finite explicit set that can only shrink.

Costs:

- current network sources are temporarily labelled migration debt even though
  they are working;
- source activation now requires catalog + binding + adapter + policy agreement;
- migrating existing sources takes more engineering than adding another direct
  HTTP function.

Those costs are intentional. At the scale PersonaLattice is targeting, source
activation must become boring and difficult to do incorrectly.
