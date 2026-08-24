#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/personalattice-launch-smoke"
API_LOG="$TMP_DIR/api.log"
WEB_LOG="$TMP_DIR/web.log"
LOGIN_HEADERS="$TMP_DIR/login.headers"
LOGIN_BODY="$TMP_DIR/login.json"
FRESH_LOGIN_HEADERS="$TMP_DIR/fresh-login.headers"
FRESH_LOGIN_BODY="$TMP_DIR/fresh-login.json"
PUBLIC_HEADERS="$TMP_DIR/public.headers"
PUBLIC_BODY="$TMP_DIR/public.html"
BACKUP_PATH="$TMP_DIR/personalattice.pre-restart.db"
RESTORE_STASH="$TMP_DIR/personalattice.original.db"
mkdir -p "$TMP_DIR"
rm -f \
  "$API_LOG" \
  "$WEB_LOG" \
  "$LOGIN_HEADERS" \
  "$LOGIN_BODY" \
  "$FRESH_LOGIN_HEADERS" \
  "$FRESH_LOGIN_BODY" \
  "$PUBLIC_HEADERS" \
  "$PUBLIC_BODY" \
  "$BACKUP_PATH" \
  "$RESTORE_STASH"

API_PID=""
WEB_PID=""
cleanup() {
  if [[ -n "$WEB_PID" ]]; then kill "$WEB_PID" 2>/dev/null || true; fi
  if [[ -n "$API_PID" ]]; then kill "$API_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

wait_for_url() {
  local url="$1"
  local attempts=40
  for ((i=1; i<=attempts; i++)); do
    if curl --silent --show-error --fail --max-time 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  echo "launch smoke failed: $url did not become ready" >&2
  return 1
}

require_header() {
  local file="$1"
  local pattern="$2"
  if ! grep -Eiq "$pattern" "$file"; then
    echo "launch smoke failed: expected response header matching $pattern" >&2
    return 1
  fi
}

start_api() {
  python -m uvicorn app.main:app \
    --app-dir services/api \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 \
    --no-proxy-headers >>"$API_LOG" 2>&1 &
  API_PID=$!
  wait_for_url "http://127.0.0.1:8000/health"
}

stop_api() {
  if [[ -z "$API_PID" ]]; then
    return 0
  fi
  kill "$API_PID" 2>/dev/null || true
  wait "$API_PID" 2>/dev/null || true
  API_PID=""
}

export PERSONALATTICE_ADMIN_USERNAME="${PERSONALATTICE_ADMIN_USERNAME:-ci-launch-admin}"
export PERSONALATTICE_COOKIE_SECURE="true"
export PERSONALATTICE_DB_PATH="${PERSONALATTICE_DB_PATH:-$TMP_DIR/personalattice.db}"
export PERSONALATTICE_CASE_RETENTION_DAYS="${PERSONALATTICE_CASE_RETENTION_DAYS:-30}"
export PERSONALATTICE_API_ORIGIN="http://127.0.0.1:8000"

if [[ -z "${PERSONALATTICE_ADMIN_PASSWORD_HASH:-}" ]]; then
  echo "launch smoke failed: PERSONALATTICE_ADMIN_PASSWORD_HASH is required" >&2
  exit 1
fi
if [[ -z "${PERSONALATTICE_LAUNCH_SMOKE_PASSWORD:-}" ]]; then
  echo "launch smoke failed: PERSONALATTICE_LAUNCH_SMOKE_PASSWORD is required" >&2
  exit 1
fi

cd "$ROOT"
python -m app.launch_preflight >/dev/null

SEEDED_CASE_ID="$(python - <<'PY'
from app.cases import CASE_STORE
from app.research import ResearchKind

record = CASE_STORE.create_payload(
    seed_kind=ResearchKind.USERNAME,
    seed_value="launch-smoke-retained",
    report_payload={
        "kind": "username",
        "normalized_value": "launch-smoke-retained",
        "observations": [],
        "warnings": [],
        "source_runs": [],
        "launch_smoke": True,
    },
)
print(record.id)
PY
)"
if [[ -z "$SEEDED_CASE_ID" ]]; then
  echo "launch smoke failed: retained case seed did not produce an id" >&2
  exit 1
fi

start_api

(
  cd "$ROOT/apps/web"
  npm run start -- --hostname 127.0.0.1 --port 3000
) >"$WEB_LOG" 2>&1 &
WEB_PID=$!
wait_for_url "http://127.0.0.1:3000/"
wait_for_url "http://127.0.0.1:3000/api/health"

curl --silent --show-error --fail \
  -D "$PUBLIC_HEADERS" \
  -o "$PUBLIC_BODY" \
  "http://127.0.0.1:3000/"
require_header "$PUBLIC_HEADERS" '^content-security-policy:'
require_header "$PUBLIC_HEADERS" '^strict-transport-security:'
require_header "$PUBLIC_HEADERS" '^x-content-type-options:[[:space:]]*nosniff'
require_header "$PUBLIC_HEADERS" '^x-frame-options:[[:space:]]*DENY'

if grep -Eiq 'csrf_token|personalattice_admin_password_hash|__Host-personalattice_session' "$PUBLIC_BODY"; then
  echo "launch smoke failed: public page contains private/session markers" >&2
  exit 1
fi

curl --silent --show-error \
  -D "$LOGIN_HEADERS" \
  -o "$LOGIN_BODY" \
  -H 'Content-Type: application/json' \
  --data "$(python -c 'import json, os; print(json.dumps({"username": os.environ["PERSONALATTICE_ADMIN_USERNAME"], "password": os.environ["PERSONALATTICE_LAUNCH_SMOKE_PASSWORD"]}))')" \
  "http://127.0.0.1:3000/api/v1/auth/login"

if ! head -n 1 "$LOGIN_HEADERS" | grep -Eq ' 200 '; then
  echo "launch smoke failed: proxied login did not return 200" >&2
  exit 1
fi

COOKIE_LINE="$(grep -i '^set-cookie:' "$LOGIN_HEADERS" | head -n 1 | tr -d '\r')"
for required in '__Host-personalattice_session=' 'Secure' 'HttpOnly' 'SameSite=strict' 'Path=/'; do
  if [[ "$COOKIE_LINE" != *"$required"* ]]; then
    echo "launch smoke failed: session cookie is missing $required" >&2
    exit 1
  fi
done
if printf '%s' "$COOKIE_LINE" | grep -Eiq '(^|;)[[:space:]]*Domain='; then
  echo "launch smoke failed: __Host- session cookie must not set Domain" >&2
  exit 1
fi

SESSION_TOKEN="$(printf '%s' "$COOKIE_LINE" | sed -E 's/^[^:]+:[[:space:]]*__Host-personalattice_session=([^;]+).*/\1/I')"
CSRF_TOKEN="$(python -c 'import json, sys; print(json.load(open(sys.argv[1]))["csrf_token"])' "$LOGIN_BODY")"
if [[ -z "$SESSION_TOKEN" || -z "$CSRF_TOKEN" ]]; then
  echo "launch smoke failed: login did not produce session and CSRF tokens" >&2
  exit 1
fi

SESSION_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -H "Cookie: __Host-personalattice_session=$SESSION_TOKEN" \
  "http://127.0.0.1:3000/api/v1/auth/session")"
if [[ "$SESSION_STATUS" != "200" ]]; then
  echo "launch smoke failed: authenticated session did not survive the web proxy" >&2
  exit 1
fi

CASE_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -H "Cookie: __Host-personalattice_session=$SESSION_TOKEN" \
  "http://127.0.0.1:3000/api/v1/cases/$SEEDED_CASE_ID")"
if [[ "$CASE_STATUS" != "200" ]]; then
  echo "launch smoke failed: retained case was not readable before restart" >&2
  exit 1
fi

stop_api
python -m app.database_backup "$PERSONALATTICE_DB_PATH" "$BACKUP_PATH" >/dev/null

mv "$PERSONALATTICE_DB_PATH" "$RESTORE_STASH"
rm -f "${PERSONALATTICE_DB_PATH}-wal" "${PERSONALATTICE_DB_PATH}-shm"
cp "$BACKUP_PATH" "$PERSONALATTICE_DB_PATH"
chmod 600 "$PERSONALATTICE_DB_PATH"

start_api

OLD_SESSION_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -H "Cookie: __Host-personalattice_session=$SESSION_TOKEN" \
  "http://127.0.0.1:3000/api/v1/auth/session")"
if [[ "$OLD_SESSION_STATUS" != "401" ]]; then
  echo "launch smoke failed: pre-restart in-memory session remained usable" >&2
  exit 1
fi

curl --silent --show-error \
  -D "$FRESH_LOGIN_HEADERS" \
  -o "$FRESH_LOGIN_BODY" \
  -H 'Content-Type: application/json' \
  --data "$(python -c 'import json, os; print(json.dumps({"username": os.environ["PERSONALATTICE_ADMIN_USERNAME"], "password": os.environ["PERSONALATTICE_LAUNCH_SMOKE_PASSWORD"]}))')" \
  "http://127.0.0.1:3000/api/v1/auth/login"

if ! head -n 1 "$FRESH_LOGIN_HEADERS" | grep -Eq ' 200 '; then
  echo "launch smoke failed: fresh proxied login after restart did not return 200" >&2
  exit 1
fi

FRESH_COOKIE_LINE="$(grep -i '^set-cookie:' "$FRESH_LOGIN_HEADERS" | head -n 1 | tr -d '\r')"
FRESH_SESSION_TOKEN="$(printf '%s' "$FRESH_COOKIE_LINE" | sed -E 's/^[^:]+:[[:space:]]*__Host-personalattice_session=([^;]+).*/\1/I')"
FRESH_CSRF_TOKEN="$(python -c 'import json, sys; print(json.load(open(sys.argv[1]))["csrf_token"])' "$FRESH_LOGIN_BODY")"
if [[ -z "$FRESH_SESSION_TOKEN" || -z "$FRESH_CSRF_TOKEN" ]]; then
  echo "launch smoke failed: fresh login did not produce session and CSRF tokens" >&2
  exit 1
fi

RESTORED_CASE_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -H "Cookie: __Host-personalattice_session=$FRESH_SESSION_TOKEN" \
  "http://127.0.0.1:3000/api/v1/cases/$SEEDED_CASE_ID")"
if [[ "$RESTORED_CASE_STATUS" != "200" ]]; then
  echo "launch smoke failed: retained case did not survive backup, restore and restart" >&2
  exit 1
fi

DELETE_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -X DELETE \
  -H "Cookie: __Host-personalattice_session=$FRESH_SESSION_TOKEN" \
  -H "X-PersonaLattice-CSRF: $FRESH_CSRF_TOKEN" \
  "http://127.0.0.1:3000/api/v1/cases/$SEEDED_CASE_ID")"
if [[ "$DELETE_STATUS" != "204" ]]; then
  echo "launch smoke failed: retained case delete did not return 204" >&2
  exit 1
fi

POST_DELETE_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -H "Cookie: __Host-personalattice_session=$FRESH_SESSION_TOKEN" \
  "http://127.0.0.1:3000/api/v1/cases/$SEEDED_CASE_ID")"
if [[ "$POST_DELETE_STATUS" != "404" ]]; then
  echo "launch smoke failed: deleted retained case remained readable" >&2
  exit 1
fi

LOGOUT_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -X POST \
  -H "Cookie: __Host-personalattice_session=$FRESH_SESSION_TOKEN" \
  -H "X-PersonaLattice-CSRF: $FRESH_CSRF_TOKEN" \
  "http://127.0.0.1:3000/api/v1/auth/logout")"
if [[ "$LOGOUT_STATUS" != "204" ]]; then
  echo "launch smoke failed: proxied logout did not return 204" >&2
  exit 1
fi

POST_LOGOUT_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -H "Cookie: __Host-personalattice_session=$FRESH_SESSION_TOKEN" \
  "http://127.0.0.1:3000/api/v1/auth/session")"
if [[ "$POST_LOGOUT_STATUS" != "401" ]]; then
  echo "launch smoke failed: revoked fresh session remained usable" >&2
  exit 1
fi

for secret in \
  "$PERSONALATTICE_LAUNCH_SMOKE_PASSWORD" \
  "$PERSONALATTICE_ADMIN_PASSWORD_HASH" \
  "$SESSION_TOKEN" \
  "$CSRF_TOKEN" \
  "$FRESH_SESSION_TOKEN" \
  "$FRESH_CSRF_TOKEN"; do
  if grep -Fq -- "$secret" "$API_LOG" "$WEB_LOG"; then
    echo "launch smoke failed: sensitive launch value appeared in process logs" >&2
    exit 1
  fi
done

printf '%s\n' "production process smoke passed"
