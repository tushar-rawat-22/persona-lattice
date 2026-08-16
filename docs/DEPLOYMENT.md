# Deployment

PersonaLattice currently deploys as two services:

- **web** — the Next.js application (`apps/web`), which serves the public synthetic preview and the private `/admin` operator UI;
- **API** — the FastAPI service (`services/api`), which owns admin authentication, protected research execution and the private retained-case database.

The public web application proxies browser calls through `/api/*` to the private API origin. This keeps the session cookie first-party to the public web origin and avoids exposing the API origin in browser configuration.

## Required production properties

M7 is intentionally a **one-admin, one-API-worker** deployment.

The current session store is process-local and fail-closed. Running multiple API workers or replicas would create inconsistent sessions because a cookie authenticated by one process is unknown to another. Do not scale the API horizontally until session records move to shared durable storage.

Retained research cases use SQLite. The database path therefore must be on protected persistent storage. A serverless/ephemeral filesystem will lose cases after restart/deploy and is not an acceptable production case store.

## API deployment

`services/api/Dockerfile` is the production container entry point. `render.yaml` provides a reference Render Blueprint using:

- one Docker web service;
- one Uvicorn worker;
- a persistent disk at `/var/data/personalattice`;
- `PERSONALATTICE_DB_PATH=/var/data/personalattice/personalattice.db`;
- secure cookies;
- administrator username/password hash supplied as deployment secrets rather than source-controlled values.

Set these secrets in the hosting control plane:

```text
PERSONALATTICE_ADMIN_USERNAME
PERSONALATTICE_ADMIN_PASSWORD_HASH
```

Generate the password hash from a trusted local checkout with:

```text
python -m app.admin_setup
```

Run that command from `services/api` with the project environment installed. It prompts without echoing the password and prints only the Argon2id hash to copy into the deployment secret store.

Production should retain:

```text
PERSONALATTICE_COOKIE_SECURE=true
PERSONALATTICE_SESSION_COOKIE=__Host-personalattice_session
PERSONALATTICE_SESSION_SECONDS=28800
```

The `__Host-` cookie form requires HTTPS, `Secure`, `Path=/`, and no `Domain` attribute. The application satisfies those attributes when `PERSONALATTICE_COOKIE_SECURE=true`.

## Web deployment

Create the Next.js project with **Root Directory** `apps/web`.

Set:

```text
NEXT_PUBLIC_API_URL=/api
PERSONALATTICE_API_ORIGIN=https://<private-api-origin>
```

`NEXT_PUBLIC_API_URL` is intentionally only `/api`; the browser never needs the API hostname. `PERSONALATTICE_API_ORIGIN` is consumed by Next.js server configuration to proxy requests.

The public root does not advertise `/admin`. That is a product choice, not a security boundary. Direct navigation to `/admin` is safe only because protected API operations still require a valid server-side admin session and protected writes require the session-linked CSRF token.

## Persistence and backup

M7 retention defaults to 30 days. Cases can also be deleted explicitly from the operator UI/API. Backups are **not enabled by application code** yet. If the hosting platform snapshots the persistent disk, those copies become an additional personal-data retention surface and must be governed before relying on them as production backups.

SQLite is not currently application-level encrypted. Do not describe M7 as providing database encryption at rest unless the selected hosting/storage layer actually provides it and that control has been verified.

## Public/private verification checklist

Before exposing the URL publicly, verify all of the following:

1. `/` and `/dashboard` contain synthetic/demo data only.
2. `/api/v1/cases` returns `401` without the admin session cookie.
3. `/api/v1/intake/preview`, `/api/v1/cases/run`, `/api/v1/files/preview` and case deletion fail without the matching CSRF header even when a valid session cookie exists.
4. `/admin` can authenticate with the configured admin username/password and rejects incorrect credentials.
5. logout invalidates the current session.
6. restarting the API invalidates existing sessions as expected.
7. creating a case, restarting/deploying the API and re-authenticating leaves the case present on persistent storage.
8. the deployed cookie is `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`, and contains only an opaque value.
9. the API is running exactly one worker/replica for M7.
10. no real credentials, database files or research outputs are committed to Git.

## Provider secrets

Optional provider credentials remain server-side environment secrets. An absent credential must disable or defer that provider rather than causing the application to fabricate enrichment.

The first production deployment does not require an external phone/email enrichment provider. Live username research works through the reviewed public-source path; phone/email coverage remains deliberately narrower until an external source passes source, license, privacy, retention and cost review.
