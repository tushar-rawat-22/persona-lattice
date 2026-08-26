#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${PERSONALATTICE_LC1_BROWSER_API_PORT:-18100}"
WEB_PORT="${PERSONALATTICE_LC1_BROWSER_WEB_PORT:-13100}"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/personalattice-lc1-browser.XXXXXX")"
chmod 700 "$TMP_DIR"
ACCEPT_ROOT="$TMP_DIR/checkout"
PYTHON="$TMP_DIR/venv/bin/python"
API_LOG="$TMP_DIR/api.log"
WEB_LOG="$TMP_DIR/web.log"
TUNNEL_LOG="$TMP_DIR/tunnel.log"
COOKIE_JAR="$TMP_DIR/cookies.txt"
LOGIN_BODY="$TMP_DIR/login.json"
URL_CASE_BODY="$TMP_DIR/url-case.json"
DOMAIN_CASE_BODY="$TMP_DIR/domain-case.json"
API_PID=""
WEB_PID=""
TUNNEL_PID=""
WORKTREE_ADDED="false"
PUBLIC_URL="${PERSONALATTICE_LC1_EXTERNAL_URL:-}"

if [[ "$(uname -s)" == "Darwin" ]]; then
  EVIDENCE_DIR="$HOME/Library/Application Support/PersonaLattice/lc1"
else
  EVIDENCE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/personalattice/lc1"
fi

cleanup() {
  if [[ -n "$TUNNEL_PID" ]]; then kill "$TUNNEL_PID" 2>/dev/null || true; wait "$TUNNEL_PID" 2>/dev/null || true; fi
  if [[ -n "$WEB_PID" ]]; then kill "$WEB_PID" 2>/dev/null || true; wait "$WEB_PID" 2>/dev/null || true; fi
  if [[ -n "$API_PID" ]]; then kill "$API_PID" 2>/dev/null || true; wait "$API_PID" 2>/dev/null || true; fi
  if [[ "$WORKTREE_ADDED" == "true" ]] && command -v git >/dev/null 2>&1; then
    git -C "$ROOT" worktree remove --force "$ACCEPT_ROOT" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

fail() {
  printf 'LC1 browser hold failed: %s\n' "$1" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command '$1' is unavailable"
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-80}"
  for ((i=1; i<=attempts; i++)); do
    if curl --silent --show-error --fail --max-time 3 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  fail "$url did not become ready"
}

require_status() {
  local expected="$1"
  local actual="$2"
  local label="$3"
  [[ "$actual" == "$expected" ]] || fail "$label returned HTTP $actual (expected $expected)"
}

start_api() {
  (
    cd "$ACCEPT_ROOT"
    "$PYTHON" -m uvicorn app.main:app \
      --app-dir services/api \
      --host 127.0.0.1 \
      --port "$API_PORT" \
      --workers 1 \
      --no-proxy-headers
  ) >>"$API_LOG" 2>&1 &
  API_PID=$!
  wait_for_url "http://127.0.0.1:$API_PORT/health"
}

start_web() {
  (
    cd "$ACCEPT_ROOT/apps/web"
    npm run start -- --hostname 127.0.0.1 --port "$WEB_PORT"
  ) >>"$WEB_LOG" 2>&1 &
  WEB_PID=$!
  wait_for_url "http://127.0.0.1:$WEB_PORT/"
  wait_for_url "http://127.0.0.1:$WEB_PORT/api/health"
}

start_quick_tunnel() {
  require_command cloudflared
  cloudflared tunnel --no-autoupdate --url "http://127.0.0.1:$WEB_PORT" >"$TUNNEL_LOG" 2>&1 &
  TUNNEL_PID=$!
  for ((i=1; i<=120; i++)); do
    PUBLIC_URL="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -n 1 || true)"
    if [[ -n "$PUBLIC_URL" ]]; then
      wait_for_url "$PUBLIC_URL/api/health" 80
      return 0
    fi
    if ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
      fail "Cloudflare Quick Tunnel exited before producing an HTTPS URL"
    fi
    sleep 0.5
  done
  fail "Cloudflare Quick Tunnel did not produce an HTTPS URL"
}

post_converged_case() {
  local kind="$1"
  local value="$2"
  local csrf="$3"
  local output="$4"
  local status
  status="$(curl --silent --show-error \
    -b "$COOKIE_JAR" \
    -o "$output" \
    -w '%{http_code}' \
    -H 'Content-Type: application/json' \
    -H "X-PersonaLattice-CSRF: $csrf" \
    --data "$(KIND="$kind" VALUE="$value" "$PYTHON" -c 'import json, os; print(json.dumps({"kind": os.environ["KIND"], "value": os.environ["VALUE"], "purpose": "public_source_research", "consent_acknowledged": False}))')" \
    "$PUBLIC_URL/api/v1/cases/run-converged")"
  require_status 200 "$status" "$kind browser seed case"
}

require_command curl
require_command git
require_command npm

cd "$ROOT"
[[ -d .git ]] || fail "run this from a PersonaLattice checkout"
[[ "$(git status --porcelain)" == "" ]] || fail "working tree must be clean before browser acceptance"
[[ "$(git rev-parse --abbrev-ref HEAD)" == "main" ]] || fail "browser acceptance must run from main"
[[ -d "$EVIDENCE_DIR" ]] || fail "LC1 host evidence directory does not exist; run scripts/lc1_host_acceptance.sh first"
SYSTEM_PYTHON="$(bash "$ROOT/scripts/lc1_select_python.sh")" || fail "Python 3.11 or newer is unavailable"

LATEST_EVIDENCE="$(find "$EVIDENCE_DIR" -maxdepth 1 -type f -name '*.json' -print | sort | tail -n 1)"
[[ -n "$LATEST_EVIDENCE" ]] || fail "no LC1 host evidence summary exists; run scripts/lc1_host_acceptance.sh first"

read -r EVIDENCE_STATUS TESTED_COMMIT < <("$SYSTEM_PYTHON" - "$LATEST_EVIDENCE" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
print(payload.get("status", ""), payload.get("tested_commit", ""))
PY
)
[[ "$EVIDENCE_STATUS" == "passed" ]] || fail "latest LC1 host evidence is not a passing run"
[[ "$TESTED_COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail "latest LC1 host evidence does not contain a valid tested commit"

git fetch --quiet origin main
git cat-file -e "$TESTED_COMMIT^{commit}" 2>/dev/null || fail "tested commit $TESTED_COMMIT is not available locally"
if ! git merge-base --is-ancestor "$TESTED_COMMIT" origin/main; then
  fail "tested commit $TESTED_COMMIT is not an ancestor of current origin/main"
fi

git worktree add --detach "$ACCEPT_ROOT" "$TESTED_COMMIT" >/dev/null
WORKTREE_ADDED="true"

"$SYSTEM_PYTHON" -m venv "$TMP_DIR/venv"
"$PYTHON" -m pip install --upgrade pip >/dev/null
"$PYTHON" -m pip install -e "$ACCEPT_ROOT/services/api" >/dev/null

export PERSONALATTICE_ADMIN_USERNAME="lc1-browser-admin"
export PERSONALATTICE_LC1_PASSWORD="$("$PYTHON" -c 'import secrets; print(secrets.token_urlsafe(24))')"
export PERSONALATTICE_ADMIN_PASSWORD_HASH="$("$PYTHON" -c 'import os; from app.admin_auth import hash_admin_password; print(hash_admin_password(os.environ["PERSONALATTICE_LC1_PASSWORD"]))')"
export PERSONALATTICE_COOKIE_SECURE="true"
export PERSONALATTICE_DB_PATH="$TMP_DIR/personalattice.db"
export PERSONALATTICE_CASE_RETENTION_DAYS="30"
export PERSONALATTICE_API_ORIGIN="http://127.0.0.1:$API_PORT"

"$PYTHON" -m app.launch_preflight >/dev/null
npm ci --prefix "$ACCEPT_ROOT/apps/web" --no-audit --no-fund >/dev/null
PERSONALATTICE_API_ORIGIN="$PERSONALATTICE_API_ORIGIN" npm run --prefix "$ACCEPT_ROOT/apps/web" build >/dev/null

start_api
start_web
if [[ -z "$PUBLIC_URL" ]]; then
  start_quick_tunnel
else
  [[ "$PUBLIC_URL" == https://* ]] || fail "PERSONALATTICE_LC1_EXTERNAL_URL must use HTTPS"
  wait_for_url "$PUBLIC_URL/api/health" 80
fi

LOGIN_STATUS="$(curl --silent --show-error \
  -c "$COOKIE_JAR" \
  -o "$LOGIN_BODY" \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data "$("$PYTHON" -c 'import json, os; print(json.dumps({"username": os.environ["PERSONALATTICE_ADMIN_USERNAME"], "password": os.environ["PERSONALATTICE_LC1_PASSWORD"]}))')" \
  "$PUBLIC_URL/api/v1/auth/login")"
require_status 200 "$LOGIN_STATUS" "browser-seed login"
CSRF_TOKEN="$("$PYTHON" - "$LOGIN_BODY" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["csrf_token"])
PY
)"

post_converged_case url 'https://github.com/octocat' "$CSRF_TOKEN" "$URL_CASE_BODY"
post_converged_case domain 'example.com' "$CSRF_TOKEN" "$DOMAIN_CASE_BODY"

printf '\nLC1 BROWSER ACCEPTANCE HOLD\n'
printf 'Tested commit: %s\n' "$TESTED_COMMIT"
printf 'Host evidence: %s\n' "$LATEST_EVIDENCE"
printf 'URL: %s/admin\n' "$PUBLIC_URL"
printf 'Username: %s\n' "$PERSONALATTICE_ADMIN_USERNAME"
printf 'Temporary password: %s\n' "$PERSONALATTICE_LC1_PASSWORD"
printf '\nThe exact host-tested commit is running with fresh octocat URL and example.com domain cases.\n'
printf 'Check Safari and Chrome: rendered source state/provenance/M5, responsive layout, keyboard/focus, loading/error/empty states, and no identity-probability claims.\n'
printf 'This URL is temporary smoke infrastructure only. Press Control-C when browser acceptance is finished.\n\n'

if [[ "$(uname -s)" == "Darwin" ]] && command -v open >/dev/null 2>&1; then
  open "$PUBLIC_URL/admin" >/dev/null 2>&1 || true
fi

while :; do
  sleep 3600 &
  wait $!
done
