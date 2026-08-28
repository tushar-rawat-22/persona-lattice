# Deployment

PersonaLattice currently runs as two application processes:

- **web** — the Next.js application in `apps/web`, including the public synthetic preview and private `/admin` operator workspace;
- **API** — the FastAPI service in `services/api`, which owns authentication, protected research execution, provider governance and retained cases.

The browser uses the web origin for `/api/*`. Next.js proxies those requests to the API. Keep that same-origin shape in production so the browser does not need the private API hostname and the admin session cookie stays first-party.

For the distinction between a temporary project demo, a stable private beta and a future multi-user SaaS deployment, read `docs/LIVE_BETA.md` first.

## Current production shape

The current release is deliberately a **one-admin, one-API-worker** product.

Session records are process-local. Do not run multiple API workers or replicas: a session created in one process is not shared with another process.

Retained cases use SQLite. `PERSONALATTICE_DB_PATH` must therefore point to protected persistent storage. An ephemeral/serverless filesystem is not an acceptable retained-case store.

This is a valid architecture for the private operator product and private beta. Horizontal scaling and multi-user tenancy are later architecture work, not launch prerequisites for the current product.

## Core server-side configuration

Required authenticated runtime configuration:

```text
PERSONALATTICE_ADMIN_USERNAME
PERSONALATTICE_ADMIN_PASSWORD_HASH
PERSONALATTICE_DB_PATH
```

Production HTTPS should retain:

```text
PERSONALATTICE_COOKIE_SECURE=true
PERSONALATTICE_SESSION_COOKIE=__Host-personalattice_session
PERSONALATTICE_SESSION_SECONDS=28800
```

Generate the admin Argon2id hash from a trusted checkout with the repository helper rather than storing a plaintext password:

```bash
cd services/api
python -m app.admin_setup
```

The plaintext password, generated hash, retained database and provider credentials must never be committed to Git.

The `__Host-` cookie form requires HTTPS, `Secure`, `Path=/` and no `Domain` attribute. Keep those properties intact.

## Web configuration

Browser code always uses the same-origin `/api` proxy. `apps/web/next.config.ts` sets `NEXT_PUBLIC_API_URL=/api` in the built application.

The Next.js server resolves its API destination in this order:

```text
PERSONALATTICE_API_ORIGIN
PERSONALATTICE_API_HOSTPORT
http://127.0.0.1:8000   # local fallback
```

For a normal hosted topology, set `PERSONALATTICE_API_ORIGIN` to the private/reachable API origin. The Render reference instead injects `PERSONALATTICE_API_HOSTPORT` from the private API service. Do not place API credentials in `NEXT_PUBLIC_*` variables.

The public root does not advertise `/admin`. That is product navigation, not a security control. `/admin` is safe to discover only because real data and mutations remain protected by server-side authentication and session-linked CSRF checks.

## Provider configuration

Optional provider credentials and operator metadata stay server-side. Absence must become an explicit not-configured/unavailable state before provider contact, not fabricated enrichment.

Current examples include:

```text
BRAVE_SEARCH_API_KEY
OPENALEX_API_KEY
COMPANIES_HOUSE_API_KEY
SEC_EDGAR_USER_AGENT
```

`BRAVE_SEARCH_API_KEY` is optional and metered; it is not required for the zero-spend baseline.

`OPENALEX_API_KEY` is used only for exact admitted OpenAlex author URLs.

`COMPANIES_HOUSE_API_KEY` is used only for exact canonical public company URLs and is sent server-side using the documented Basic-auth form. Do not use company authentication codes or user credentials.

`SEC_EDGAR_USER_AGENT` is non-secret operator identity metadata, not an API credential. It must contain a maintainable PersonaLattice/operator identity and real contact email. If it is absent or malformed, SEC execution must fail before network contact.

Re-check provider-specific source-admission records and current provider documentation before changing these requirements.

## Option A — controlled host + named Cloudflare Tunnel

This is the lowest-churn path for a stable private beta because LC1 already validated the production-shaped application on the candidate host.

Keep API and web bound to local/private interfaces. Publish the web process through a named Cloudflare Tunnel and a hostname on a domain/zone that you control. Keep browser API calls on the same-origin `/api` path.

Do not use a random `trycloudflare.com` Quick Tunnel as the permanent beta endpoint. Cloudflare documents Quick Tunnels as testing/development infrastructure. They remain useful for short-lived synthetic demos and smoke tests.

The candidate host must remain online whenever the beta should be reachable. The local SQLite database and its backups remain operator-managed data surfaces.

## Option B — hosted private beta on Render

The repository keeps an optional reference topology at:

```text
deploy/render-paid.yaml
```

It is deliberately outside the zero-spend baseline.

The reference uses one API service with a persistent disk for SQLite and one web service. Render services have an ephemeral filesystem by default, and current Render persistent disks attach to paid services. Do not move the current SQLite API to a free ephemeral web instance and describe retained cases as durable.

A hosted beta can initially use the generated `onrender.com` hostname; a custom domain is optional. Re-check Render's current plans/pricing before provisioning because the repository does not freeze vendor pricing as an application contract.

## Persistence and backups

Retained research cases default to bounded retention and support explicit deletion. The database still needs an operational backup policy if the private beta will hold evidence you care about.

A backup is another retained-data copy. Store it with equivalent access controls and deletion discipline.

SQLite is not application-level encrypted. Do not claim database encryption at rest unless the chosen host/storage layer actually provides that control and it has been verified.

For the candidate-host path, use the repository's verified SQLite backup/restore tooling rather than copying an active database file casually.

## Stable-beta release checklist

Before calling a permanent URL a live private beta, verify the following on the exact release SHA:

1. HTTPS is stable and the temporary smoke tunnel is not being presented as production.
2. `/` and other public/demo routes expose synthetic material only.
3. unauthenticated `/api/v1/cases` and protected mutations fail closed.
4. authenticated writes fail without the matching CSRF token.
5. `/admin` accepts the configured admin credentials and rejects incorrect credentials.
6. the session cookie is `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/` and opaque.
7. there is exactly one API worker/replica.
8. creating a case, restarting the API, signing in again and reopening the case proves persistent storage.
9. a verified backup/restore succeeds on the deployed storage path.
10. one bounded research case shows source-state, provenance and non-probabilistic M5 output correctly.
11. Safari and Chrome render the current operator workspace correctly, including loading/error/empty/session states.
12. the exact release SHA and rollback point are recorded in `docs/CONTINUITY.md`.

Repository CI is necessary but not sufficient for this deployed-environment gate.

## What changes for a future SaaS deployment

Do not horizontally scale the current runtime by simply increasing worker count.

Before multi-user production, PersonaLattice needs shared durable session/auth state, tenant-aware authorization, a concurrent production datastore, production backup/restore and deletion operations, observability/incident handling, and the relevant privacy/legal operating documents.

Those are future company/product milestones. They do not block showing or operating the current one-admin private beta.