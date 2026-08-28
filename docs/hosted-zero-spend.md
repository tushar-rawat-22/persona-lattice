# Zero-spend hosted demo architecture

PersonaLattice's hosted project/demo path must remain usable at ₹0 and must not pretend that a free ephemeral filesystem is durable.

## Chosen shape

The public read-only product demo is served from a free edge/static deployment and contains only synthetic fixtures. It may show the same hierarchy, source-state vocabulary, provenance, contradictions and M5 factor presentation as the private operator workspace, but it cannot start research, mutate retained cases, upload evidence or expose protected data.

The private one-admin API remains a separate authenticated service. For a no-spend hosted beta, its retained evidence store must move away from local ephemeral SQLite before using a free stateless web host. The preferred migration target is a remote libSQL/Turso database because its Python driver is SQLite-compatible and the current free tier provides durable cloud storage without Render's 30-day free-Postgres expiry.

## Why not free Render SQLite

Render free web services spin down after inactivity and lose local filesystem changes on restarts, redeploys and spin-down. That makes a local SQLite case database unsuitable for retained evidence.

Render free Postgres is also not a durable baseline because free databases expire after 30 days.

## Why Turso for the retained store

Turso's current free tier provides cloud databases with a 5 GB storage allowance and its Python libSQL client exposes a sqlite3-compatible API. This makes it a smaller migration from PersonaLattice's existing storage layer than replacing every persistence contract with a new relational abstraction.

The migration must still be test-first. Do not switch production storage until existing retention, migration, delete, backup/export and fail-closed database tests pass against the remote-store adapter.

## Public demo boundary

The hosted public surface must remain non-operational:

- synthetic fixture data only;
- no real-person seed form;
- no provider execution;
- no uploads;
- no retained-case mutation;
- no admin session token in public JavaScript;
- no hidden API endpoint that accepts public research jobs;
- clear link to the private admin login without exposing credentials.

The point of the demo is to show what the operator sees and how PersonaLattice reasons about evidence, not to provide anonymous background-check execution.

## Hosting sequence

1. Finish the public read-only demo surface and its regression contract.
2. Add an edge/static deployment target that works on a provider-generated hostname without a purchased domain.
3. Add a remote libSQL storage adapter behind the existing storage contract and keep local SQLite as the zero-spend local mode.
4. Deploy the private API on a free Python web-service tier using the remote store; accept cold starts rather than faking always-on compute with keep-alive traffic.
5. Run the full deployed launch gate: auth, CSRF, synthetic public boundary, exact research, retained-case reopen, restart persistence and browser checks.
6. Record the deployed URLs and release SHA in `docs/CONTINUITY.md`.

This architecture is for a project/private beta. A commercial multi-user launch remains a later milestone with paid/reliable infrastructure, shared sessions, tenant authorization, production backups and incident operations.
