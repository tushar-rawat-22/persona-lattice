# Optional paid Render deployment reference

PersonaLattice's default operating path is the zero-spend local setup in
`docs/ZERO_SPEND_RUNBOOK.md`. This document preserves the previously reviewed
Render topology for an operator who deliberately chooses paid private compute
and persistent storage.

The reference Blueprint now lives at `deploy/render-paid.yaml`; there is no
repository-root `render.yaml`. That separation is intentional so a paid topology
cannot be mistaken for the baseline deployment contract.

Do not put passwords, API keys, real research identifiers or retained-case data
into Git, screenshots or deployment notes.

## 1. Pre-deploy repository gate

Use this optional topology only from a green `main` commit. The required checks
include:

- API tests on Python 3.11 and 3.13;
- Python dependency checks and audit;
- Ruff;
- web `npm ci` and production dependency audit;
- web lint, typecheck and production build;
- production API image build.

The deployment contract tests assert that this reference keeps the research API
private, retains the reviewed port/cookie/proxy-header boundaries, and remains
outside the repository root.

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
Argon2 hash. Copy that hash directly into the deployment secret field.

## 3. Cost boundary

The reference Blueprint pins both services to Render's `starter` instance type
and attaches a 1 GB persistent disk to the private API. Treat this as a **paid
optional topology**, not a zero-cost deployment.

Before using it, re-check current Render pricing, private-service availability,
persistent-disk pricing and terms in Render's primary documentation. Do not rely
on prices or free-tier assumptions recorded in this repository.

Do not convert the private API into a public service merely to chase a free tier.
That would change the reviewed exposure boundary and requires a separate security
design.

## 4. Apply the optional Blueprint

If the paid topology is deliberately selected, create a Render Blueprint from:

```text
deploy/render-paid.yaml
```

Review the resources and price estimate before applying it. The expected topology
is:

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

The API must remain a private service and must not receive a public backend URL.

## 5. Enter deployment secrets

The reference marks these values `sync: false`:

- `PERSONALATTICE_ADMIN_USERNAME`;
- `PERSONALATTICE_ADMIN_PASSWORD_HASH`;
- `BRAVE_SEARCH_API_KEY` — optional; leave unconfigured unless the metered search
  integration is deliberately enabled.

Do not enter the plaintext admin password as the password-hash value.

## 6. Public-boundary verification

After deployment, run the committed verifier against only the public web origin:

```bash
python3 scripts/verify_public_boundary.py https://YOUR-PUBLIC-WEB-ORIGIN
```

The verifier performs no research and sends no credentials. It checks the public
shell/security headers plus anonymous denial for session, retained-case and audit
reads. A failure is a deployment blocker.

## 7. Admin acceptance

Use only an operator-controlled identifier for the first live test.

1. open `/admin` on the public web origin;
2. authenticate with the configured operator account;
3. run one small self-audit using an identifier you control;
4. confirm returned evidence remains attributable and M5 remains
   uncalibrated/non-identity;
5. delete the retained test case;
6. log out and confirm authentication is required again;
7. rerun the public-boundary verifier.

## 8. Operational invariants

The API intentionally uses one worker because authenticated sessions are held in
process memory. Do not increase worker count or horizontally scale without first
moving session state behind a reviewed shared server-side store.

The API runs Uvicorn with `--no-proxy-headers`; authentication must not depend on
caller-controlled forwarded headers. SQLite with one persistent disk is a
single-instance design. Backup/restore must be reviewed against the storage
provider actually selected.

## 9. Closure record

If this optional hosted topology is used, record only public-safe facts such as
deployment date, exact `main` commit and public-boundary verifier result. Never
record the admin password/hash, optional API key, session cookie, CSRF token,
real test identifier or provider payload.
