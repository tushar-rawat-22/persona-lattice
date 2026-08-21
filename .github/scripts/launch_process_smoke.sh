#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/personalattice-launch-smoke"
API_LOG="$TMP_DIR/api.log"
WEB_LOG="$TMP_DIR/web.log"
LOGIN_HEADERS="$TMP_DIR/login.headers"
LOGIN_BODY="$TMP_DIR/login.json"
PUBLIC_HEADERS="$TMP_DIR/public.headers"
PUBLIC_BODY="$TMP_DIR/public.html"
mkdir -p "$TMP_DIR"
rm -f "$API_LOG" "$WEB_LOG" "$LOGIN_HEADERS" "$LOGIN_BODY" "$PUBLIC_HEADERS" "$PUBLIC_BODY"

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

python -m uvicorn app.main:app \
  --app-dir services/api \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 1 \
  --no-proxy-headers >"$API_LOG" 2>&1 &
API_PID=$!
wait_for_url "http://127.0.0.1:8000/health"

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

LOGOUT_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -X POST \
  -H "Cookie: __Host-personalattice_session=$SESSION_TOKEN" \
  -H "X-PersonaLattice-CSRF: $CSRF_TOKEN" \
  "http://127.0.0.1:3000/api/v1/auth/logout")"
if [[ "$LOGOUT_STATUS" != "204" ]]; then
  echo "launch smoke failed: proxied logout did not return 204" >&2
  exit 1
fi

POST_LOGOUT_STATUS="$(curl --silent --show-error -o /dev/null -w '%{http_code}' \
  -H "Cookie: __Host-personalattice_session=$SESSION_TOKEN" \
  "http://127.0.0.1:3000/api/v1/auth/session")"
if [[ "$POST_LOGOUT_STATUS" != "401" ]]; then
  echo "launch smoke failed: revoked session remained usable" >&2
  exit 1
fi

for secret in \
  "$PERSONALATTICE_LAUNCH_SMOKE_PASSWORD" \
  "$PERSONALATTICE_ADMIN_PASSWORD_HASH" \
  "$SESSION_TOKEN" \
  "$CSRF_TOKEN"; do
  if grep -Fq -- "$secret" "$API_LOG" "$WEB_LOG"; then
    echo "launch smoke failed: sensitive launch value appeared in process logs" >&2
    exit 1
  fi
done

printf '%s\n' "production process smoke passed"
