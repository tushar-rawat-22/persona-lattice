# Zero-spend operating baseline

PersonaLattice does not require paid hosting, a paid database, paid proxy infrastructure or paid enrichment to run. The baseline is the local one-admin product on hardware the operator already controls. Optional metered services must not become a prerequisite for the rest of the system.

This runbook is the default operating path. `docs/DEPLOYMENT_RUNBOOK.md` describes an optional paid Render topology and is not the baseline.

## Prerequisites

- Python 3.11 or newer;
- Node.js 24;
- the repository checkout;
- local disk space for the SQLite case store and temporary upload staging.

No external database or hosted service is required.

## Install the API

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -e "./services/api[dev]"
```

Run the API tests before using the private workflow:

```bash
.venv/bin/pytest services/api/tests
```

## Configure the private admin locally

Generate an Argon2 password hash without writing the plaintext password to disk:

```bash
.venv/bin/python -m app.admin_hash_cli
```

Set the local operator configuration in the shell that will start the API. Replace the example username and hash with your own values. Do not commit them.

```bash
export PERSONALATTICE_ADMIN_USERNAME='admin'
export PERSONALATTICE_ADMIN_PASSWORD_HASH='<argon2-hash>'
export PERSONALATTICE_COOKIE_SECURE='false'
export PERSONALATTICE_DB_PATH="$PWD/.local/personalattice.db"
export PERSONALATTICE_UPLOAD_DIR="$PWD/.local/uploads"
mkdir -p "$PWD/.local/uploads"
```

`BRAVE_SEARCH_API_KEY` is deliberately omitted. Brave is optional and metered; without the key the rest of PersonaLattice remains usable.

## Start the API

```bash
.venv/bin/uvicorn app.main:app \
  --app-dir services/api \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 1 \
  --no-proxy-headers
```

Binding to `127.0.0.1` keeps the API local. Do not expose port 8000 directly to an untrusted network.

## Start the web application

In a second shell:

```bash
cd apps/web
npm ci
npm run dev
```

The development web app proxies `/api` to `http://127.0.0.1:8000` by default. Open:

```text
http://127.0.0.1:3000
```

Use `/admin` for the private operator workflow.

## Local data and cleanup

The SQLite database and upload-review staging path in the commands above live under `.local/`. Keep that directory out of backups or sync tools unless you deliberately want retained research data copied elsewhere.

Cases use the configured retention policy and explicit deletion controls. Upload review state is short-lived. Uploaded content remains untrusted input and does not authorize research until a candidate is explicitly confirmed and a separate run action is performed.

## What zero-spend means

The baseline must continue to work when all optional paid or metered integrations are absent. In particular:

- no Brave key is required;
- no hosted database is required;
- no hosted web/API service is required;
- no paid proxy or enrichment service is required;
- a missing optional service is represented as unavailable/not configured rather than breaking the investigation pipeline.

Public-source services used without credentials can still impose their own rate limits or change their terms. Those are source-availability constraints, not permission to add a paid dependency to the baseline.

## Optional hosting

Hosting is a separate operational choice. The repository keeps the previously reviewed paid Render design at `deploy/render-paid.yaml` only as an explicit reference. It is not auto-discovered from the repository root and is not required to use PersonaLattice.

Do not call a hosted option "zero cost" unless its current service, storage, egress and sleep/retention limits have been rechecked from the provider's primary documentation at deployment time.
