# Private beta launch runbook

This runbook is for the current one-admin PersonaLattice product. It is a launch gate, not a claim that M10 is calibrated or that the system can make identity-probability claims.

The required baseline stays zero-spend. A public hostname or domain is an operating choice; do not call a paid domain or paid hosting tier part of the zero-spend baseline.

## Before starting

Use one machine that you control for the API, web process and SQLite case store. Keep the API on loopback. Publish the web process through the reviewed HTTPS route; do not expose the API port directly to the public internet.

Create the admin password hash interactively and keep the plaintext password out of shell history and files:

```bash
.venv/bin/python -m app.admin_hash_cli
```

Set the production environment in the process manager or private shell. At minimum:

```bash
export PERSONALATTICE_ADMIN_USERNAME='admin'
export PERSONALATTICE_ADMIN_PASSWORD_HASH='<argon2-hash>'
export PERSONALATTICE_COOKIE_SECURE='true'
export PERSONALATTICE_DB_PATH='/absolute/private/path/personalattice.db'
export PERSONALATTICE_CASE_RETENTION_DAYS='30'
export PERSONALATTICE_API_ORIGIN='http://127.0.0.1:8000'
```

Optional provider keys stay server-side. Their absence must not break the required baseline.

## Run the launch preflight

Run this before starting the public HTTPS route:

```bash
.venv/bin/python -m app.launch_preflight
```

The command exits non-zero for an unsafe production shape. It requires a valid Argon2 admin hash, a secure `__Host-` session cookie, an absolute persistent SQLite path, a valid retention period and a loopback API origin. Its output reports only whether optional integrations are configured; it never prints provider key values.

Do not bypass this command to get a launch through.

## Back up retained cases

Stop the API before taking the launch backup. Copy the SQLite database to a path on the same private machine that is not served by the web application:

```bash
cp "$PERSONALATTICE_DB_PATH" "$PERSONALATTICE_DB_PATH.pre-launch"
```

If the database does not exist yet, record that this is a fresh launch rather than creating an empty backup file.

## Start the services

Start the API on loopback with one worker:

```bash
.venv/bin/uvicorn app.main:app \
  --app-dir services/api \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 1 \
  --no-proxy-headers
```

Build and start the web process with the same loopback API origin:

```bash
cd apps/web
npm ci
npm run build
PERSONALATTICE_API_ORIGIN='http://127.0.0.1:8000' npm run start
```

The public HTTPS route should target the web process only. The web application proxies `/api/*` to the loopback API.

## Smoke test from an external browser

Do not mark the beta live until all of these pass from a browser that is not using the server's localhost address:

1. The public route loads without exposing case data, provider keys, environment values or admin session state.
2. `/admin` requires authentication. A wrong password does not create a session.
3. A correct login sets a Secure, HttpOnly, SameSite=Strict session cookie and returns a CSRF token through the authenticated session flow.
4. A write without the CSRF header is rejected. The same write with the current CSRF token succeeds.
5. Run one bounded test for each active explicit research kind exposed by the operator selector. Provider unavailability is acceptable only when it appears as the existing typed source state rather than an application error.
6. Open the retained case from the case list. Confirm evidence fields, canonical source locators, source-run reasons, pivot provenance and M5 rationale render without browser-side identity claims.
7. Exercise reviewed-document intake with a non-sensitive test document: preview, confirm the server-owned candidate, promote it and run the explicit research action.
8. Delete a retained test case and confirm it disappears from the metadata-only case list. Confirm an older pending case request cannot restore it.
9. Log out and confirm the previous session cannot read or mutate private routes.
10. Restart the API. Confirm old in-memory sessions are invalidated by design and retained SQLite cases still exist.
11. Check the application logs. They must not contain the admin password/hash, session or CSRF tokens, provider keys, raw upload content or complete provider response payloads.

Use deliberately non-sensitive test identifiers for the launch smoke. Do not turn the smoke test into a real-person investigation.

## Retention and expiry check

Use the existing automated tests for exact expiry boundaries. For the launch machine, confirm the configured retention period is the intended value and that an expired test case is purged through the normal case-store path. Do not edit SQLite rows manually in production to prove expiry.

## Rollback

Rollback is for a failed deployment, not a routine way to hide a failing test.

1. Disable the public HTTPS route.
2. Stop the web and API processes.
3. Preserve the failed database and logs for diagnosis.
4. Check out the previously verified `main` commit.
5. Restore the pre-launch database copy only if the failed build changed the persistent store and the previous version requires the older state.
6. Run `python -m app.launch_preflight` again.
7. Start the API and web processes locally and repeat the login/session/case smoke before re-enabling the public route.

Never solve a failed migration by deleting the evidence database.

## Launch decision

`LAUNCH_CANDIDATE_1` is a repository/software gate. The private beta is not live until the candidate also passes the external-browser smoke test on the actual HTTPS route.

Real M10 evidence remains a separate validation gate. Until representative labelled evidence exists, describe PersonaLattice as evidence-assisted research with explicit uncertainty, not as a calibrated identity system.
