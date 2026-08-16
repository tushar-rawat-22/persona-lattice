# PersonaLattice private V1 deployment runbook

This runbook deploys the public product shell and the one-admin private research
backend defined by `render.yaml`. Do not put passwords, API keys, real research
identifiers or retained-case data into Git, screenshots or deployment notes.

## 1. Pre-deploy repository gate

Deploy only from a green `main` commit. The required checks are:

- API tests on Python 3.11;
- API tests on Python 3.13;
- Ruff;
- web `npm ci`;
- web lint;
- web typecheck;
- web production build.

The Blueprint contract tests also assert that the research API is a Render
private service, uses port `10001`, retains a persistent data disk, does not
hardcode deployment secrets and does not trust forwarded proxy headers.

## 2. Generate the admin password hash locally

Never enter the plaintext admin password into Git or this document. From the
repository root, with the API development environment installed:

```bash
.venv/bin/python -m app.admin_hash_cli
```

If the editable package is not installed yet:

```bash
python3 -m venv .venv
.venv/bin/pip install -e "./services/api[dev]"
.venv/bin/python -m app.admin_hash_cli
```

The command asks for the password twice without echoing it and prints only the
Argon2 hash. Copy that hash directly into the deployment secret field. Do not
save it in a tracked file.

## 3. Create the Render Blueprint

In the Render Dashboard:

1. create a new Blueprint;
2. connect `tushar-rawat-22/persona-lattice`;
3. use the `main` branch and the repository-root `render.yaml`;
4. review the resources before applying them.

The expected topology is:

```text
public internet
      |
      v
personalattice-web     Render web service
      |
      | /api over Render private network
      v
personalattice-api     Render private service, port 10001
      |
      v
persistent case disk
```

`personalattice-api` must be shown as a **private service**, not a web service.
It should not receive a public `onrender.com` URL.

## 4. Enter deployment secrets

Render prompts for Blueprint variables marked `sync: false` during initial
creation. Enter:

- `PERSONALATTICE_ADMIN_USERNAME` — choose the private operator username;
- `PERSONALATTICE_ADMIN_PASSWORD_HASH` — paste the Argon2 hash generated above;
- `BRAVE_SEARCH_API_KEY` — optional; leave unconfigured if licensed broad
  public-web discovery is not being enabled yet.

Do not enter the plaintext admin password as the password-hash value.

The web service receives the API's private `hostport` from the Blueprint. It
does not need a browser-visible backend URL or backend credential.

## 5. First public-boundary verification

After Render reports the public web service deployed, copy only its public HTTPS
origin, for example `https://your-site.example`, and run:

```bash
python3 scripts/verify_public_boundary.py https://YOUR-PUBLIC-WEB-ORIGIN
```

The verifier performs no research and sends no credentials. It checks that:

- the public shell returns HTTP 200;
- the expected browser security headers are present;
- anonymous session inspection returns 401;
- anonymous retained-case listing returns 401;
- anonymous audit listing returns 401;
- those denial responses are `Cache-Control: no-store` and contain only the
  expected authentication error.

A failure is a deployment blocker. Do not run real research until this passes.

## 6. Admin acceptance test

Use only an operator-controlled identifier for the first live test.

1. open the public web origin;
2. enter `/admin`;
3. log in with the configured admin username and plaintext password;
4. confirm the private console loads;
5. run one small self-audit with an identifier you control;
6. confirm every returned fact has an attributable source and that M5 output is
   labelled uncalibrated/non-identity;
7. delete the retained test case;
8. log out;
9. refresh `/admin` and confirm authentication is required again;
10. rerun `scripts/verify_public_boundary.py`.

Do not use another person's identifier for the deployment smoke test. The point
of this run is to validate infrastructure and authorization, not research
coverage.

## 7. Production invariants

The current V1 intentionally has one API worker because authenticated sessions
are held in process memory. A restart logs the operator out. Do not increase the
worker count or horizontally scale the private API without first moving session
state to a shared server-side store.

The private API deliberately runs Uvicorn with `--no-proxy-headers`. Authentication
must not depend on caller-controlled `X-Forwarded-*` values. Repeated failed
password checks receive bounded escalating delay instead of a persistent hard
lockout, avoiding a trivial denial-of-service against the only admin account.

The persistent disk is the retained-case store. Do not scale the current SQLite
service to multiple instances. Backup/restore policy must be reviewed against
the actual Render disk and snapshot configuration after the service exists.

## 8. Closure record

After the hosted acceptance test passes, record only public-safe operational
facts in the repository, such as:

- deployed public origin;
- deployment date;
- exact `main` commit;
- public-boundary verifier result;
- whether Brave discovery was enabled;
- production-only defects and their fixes.

Never record the admin password/hash, Brave key, session cookie, CSRF token,
real test identifier or provider payload in the repository.
