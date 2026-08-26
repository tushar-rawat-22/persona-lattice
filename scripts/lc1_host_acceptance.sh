#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${PERSONALATTICE_LC1_API_PORT:-18000}"
WEB_PORT="${PERSONALATTICE_LC1_WEB_PORT:-13000}"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/personalattice-lc1.XXXXXX")"
chmod 700 "$TMP_DIR"
ACCEPT_ROOT="$TMP_DIR/checkout"
PYTHON="$TMP_DIR/venv/bin/python"
API_LOG="$TMP_DIR/api.log"
WEB_LOG="$TMP_DIR/web.log"
TUNNEL_LOG="$TMP_DIR/tunnel.log"
COOKIE_JAR="$TMP_DIR/cookies.txt"
LOGIN_BODY="$TMP_DIR/login.json"
FRESH_LOGIN_BODY="$TMP_DIR/fresh-login.json"
URL_CASE_BODY="$TMP_DIR/url-case.json"
DOMAIN_CASE_BODY="$TMP_DIR/domain-case.json"
UPLOAD_PREVIEW_BODY="$TMP_DIR/upload-preview.json"
DOCUMENT_CASE_BODY="$TMP_DIR/document-case.json"
PUBLIC_HEADERS="$TMP_DIR/public.headers"
BACKUP_PATH="$TMP_DIR/personalattice.pre-restart.db"
RESTORE_STASH="$TMP_DIR/personalattice.original.db"
TEST_DOC="$TMP_DIR/lc1-test.txt"
API_PID=""
WEB_PID=""
TUNNEL_PID=""
PUBLIC_URL="${PERSONALATTICE_LC1_EXTERNAL_URL:-}"
WORKTREE_ADDED="false"

if [[ "$(uname -s)" == "Darwin" ]]; then
  EVIDENCE_DIR="$HOME/Library/Application Support/PersonaLattice/lc1"
else
  EVIDENCE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/personalattice/lc1"
fi
mkdir -p "$EVIDENCE_DIR"
chmod 700 "$EVIDENCE_DIR"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_PATH="$EVIDENCE_DIR/$RUN_ID.json"

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

fail() {
  printf 'LC1 host acceptance failed: %s\n' "$1" >&2
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

json_value() {
  local path="$1"
  local file="$2"
  "$PYTHON" - "$path" "$file" <<'PY'
import json
import sys

path, filename = sys.argv[1:]
value = json.load(open(filename, encoding="utf-8"))
for part in path.split("."):
    if isinstance(value, list):
        value = value[int(part)]
    else:
        value = value[part]
if isinstance(value, bool):
    print("true" if value else "false")
elif value is None:
    print("null")
else:
    print(value)
PY
}

validate_converged_case() {
  local file="$1"
  local expected_kind="$2"
  "$PYTHON" - "$file" "$expected_kind" <<'PY'
import json
import sys

filename, expected_kind = sys.argv[1:]
payload = json.load(open(filename, encoding="utf-8"))
report = payload["report"]["converged_report"]
assert report["seed"]["kind"] == expected_kind
assert report["report_version"] == "private-converged-evidence-report-v1"
assert report["executive_summary"]["identity_probability"] is None
assert report["executive_summary"]["identity_claim"] is False
assert report["provenance_rule"]
assert "m5" in report and isinstance(report["m5"], dict)
assert report["nodes"], "converged report has no research nodes"
for node in report["nodes"]:
    assert "source_runs" in node and isinstance(node["source_runs"], dict)
    assert "observations" in node and isinstance(node["observations"], list)
for decision in report["lead_graph"]["decisions"]:
    assert "source_observation_index" in decision
    assert "source_field" in decision
    assert "source" not in decision
    assert "source_locator" not in decision
print(payload["id"])
PY
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

stop_api() {
  if [[ -n "$API_PID" ]]; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
    API_PID=""
  fi
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

login() {
  local output="$1"
  local status
  status="$(curl --silent --show-error \
    -c "$COOKIE_JAR" \
    -o "$output" \
    -w '%{http_code}' \
    -H 'Content-Type: application/json' \
    --data "$("$PYTHON" -c 'import json, os; print(json.dumps({"username": os.environ["PERSONALATTICE_ADMIN_USERNAME"], "password": os.environ["PERSONALATTICE_LC1_PASSWORD"]}))')" \
    "$PUBLIC_URL/api/v1/auth/login")"
  require_status 200 "$status" "admin login"
  json_value csrf_token "$output"
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
  require_status 200 "$status" "$kind converged case"
}

require_command curl
require_command git
require_command npm

cd "$ROOT"
[[ -d .git ]] || fail "run this from a PersonaLattice checkout"
[[ "$(git status --porcelain)" == "" ]] || fail "working tree must be clean before LC1 acceptance"
[[ "$(git rev-parse --abbrev-ref HEAD)" == "main" ]] || fail "LC1 acceptance must run from main"
SYSTEM_PYTHON="$(bash "$ROOT/scripts/lc1_select_python.sh")" || fail "Python 3.11 or newer is unavailable"

git fetch --quiet origin main
git merge --ff-only --quiet origin/main
TESTED_COMMIT="$(git rev-parse HEAD)"
git worktree add --detach "$ACCEPT_ROOT" "$TESTED_COMMIT" >/dev/null
WORKTREE_ADDED="true"

"$SYSTEM_PYTHON" -m venv "$TMP_DIR/venv"
"$PYTHON" -m pip install --upgrade pip >/dev/null
"$PYTHON" -m pip install -e "$ACCEPT_ROOT/services/api" >/dev/null

export PERSONALATTICE_ADMIN_USERNAME="lc1-acceptance-admin"
export PERSONALATTICE_LC1_PASSWORD="$("$PYTHON" -c 'import secrets; print(secrets.token_urlsafe(32))')"
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

curl --silent --show-error --fail -D "$PUBLIC_HEADERS" -o /dev/null "$PUBLIC_URL/"
for header in \
  '^content-security-policy:' \
  '^strict-transport-security:' \
  '^x-content-type-options:[[:space:]]*nosniff' \
  '^x-frame-options:[[:space:]]*DENY'; do
  grep -Eiq "$header" "$PUBLIC_HEADERS" || fail "external response is missing security header matching $header"
done

CSRF_TOKEN="$(login "$LOGIN_BODY")"

post_converged_case url 'https://github.com/octocat' "$CSRF_TOKEN" "$URL_CASE_BODY"
URL_CASE_ID="$(validate_converged_case "$URL_CASE_BODY" url)"

post_converged_case domain 'example.com' "$CSRF_TOKEN" "$DOMAIN_CASE_BODY"
DOMAIN_CASE_ID="$(validate_converged_case "$DOMAIN_CASE_BODY" domain)"

cat >"$TEST_DOC" <<'EOF'
PersonaLattice LC1 non-sensitive review fixture.
Public profile: https://github.com/octocat
EOF

UPLOAD_STATUS="$(curl --silent --show-error \
  -b "$COOKIE_JAR" \
  -o "$UPLOAD_PREVIEW_BODY" \
  -w '%{http_code}' \
  -H "X-PersonaLattice-CSRF: $CSRF_TOKEN" \
  -F 'purpose=public_source_research' \
  -F 'consent_acknowledged=false' \
  -F "files=@$TEST_DOC;type=text/plain" \
  "$PUBLIC_URL/api/v1/files/preview")"
require_status 200 "$UPLOAD_STATUS" "reviewed-document preview"

read -r ARTIFACT_ID CANDIDATE_ID < <("$PYTHON" - "$UPLOAD_PREVIEW_BODY" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
for artifact in payload["artifacts"]:
    for candidate in artifact["candidates"]:
        if candidate.get("candidate_type") == "identifier" and candidate.get("identifier_kind") == "url":
            print(artifact["artifact_id"], candidate["candidate_id"])
            raise SystemExit(0)
raise SystemExit("no URL review candidate was extracted from the LC1 fixture")
PY
)
[[ -n "$ARTIFACT_ID" && -n "$CANDIDATE_ID" ]] || fail "reviewed-document preview did not return a URL candidate"

for action in confirm promote; do
  status="$(curl --silent --show-error \
    -b "$COOKIE_JAR" \
    -o /dev/null \
    -w '%{http_code}' \
    -X POST \
    -H "X-PersonaLattice-CSRF: $CSRF_TOKEN" \
    "$PUBLIC_URL/api/v1/files/review/$ARTIFACT_ID/$CANDIDATE_ID/$action")"
  require_status 200 "$status" "reviewed-document $action"
done

DOCUMENT_STATUS="$(curl --silent --show-error \
  -b "$COOKIE_JAR" \
  -o "$DOCUMENT_CASE_BODY" \
  -w '%{http_code}' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H "X-PersonaLattice-CSRF: $CSRF_TOKEN" \
  --data '{"mode":"converged","purpose":"public_source_research","consent_acknowledged":false}' \
  "$PUBLIC_URL/api/v1/files/review/$ARTIFACT_ID/$CANDIDATE_ID/run-case")"
require_status 200 "$DOCUMENT_STATUS" "reviewed-document explicit research"
DOCUMENT_CASE_ID="$(json_value case_id "$DOCUMENT_CASE_BODY")"

for case_id in "$URL_CASE_ID" "$DOMAIN_CASE_ID" "$DOCUMENT_CASE_ID"; do
  status="$(curl --silent --show-error -b "$COOKIE_JAR" -o /dev/null -w '%{http_code}' "$PUBLIC_URL/api/v1/cases/$case_id")"
  require_status 200 "$status" "retained case $case_id before restart"
done

OLD_CSRF_TOKEN="$CSRF_TOKEN"
OLD_SESSION_VALUE="$(awk '$6 == "__Host-personalattice_session" {print $7}' "$COOKIE_JAR" | tail -n 1)"

stop_api
"$PYTHON" -m app.database_backup "$PERSONALATTICE_DB_PATH" "$BACKUP_PATH" >/dev/null
mv "$PERSONALATTICE_DB_PATH" "$RESTORE_STASH"
rm -f "${PERSONALATTICE_DB_PATH}-wal" "${PERSONALATTICE_DB_PATH}-shm"
cp "$BACKUP_PATH" "$PERSONALATTICE_DB_PATH"
chmod 600 "$PERSONALATTICE_DB_PATH"
start_api

OLD_SESSION_STATUS="$(curl --silent --show-error -b "$COOKIE_JAR" -o /dev/null -w '%{http_code}' "$PUBLIC_URL/api/v1/auth/session")"
require_status 401 "$OLD_SESSION_STATUS" "pre-restart in-memory session"

rm -f "$COOKIE_JAR"
FRESH_CSRF_TOKEN="$(login "$FRESH_LOGIN_BODY")"
FRESH_SESSION_VALUE="$(awk '$6 == "__Host-personalattice_session" {print $7}' "$COOKIE_JAR" | tail -n 1)"

for case_id in "$URL_CASE_ID" "$DOMAIN_CASE_ID" "$DOCUMENT_CASE_ID"; do
  status="$(curl --silent --show-error -b "$COOKIE_JAR" -o /dev/null -w '%{http_code}' "$PUBLIC_URL/api/v1/cases/$case_id")"
  require_status 200 "$status" "retained case $case_id after restore/restart"
done

for case_id in "$URL_CASE_ID" "$DOMAIN_CASE_ID" "$DOCUMENT_CASE_ID"; do
  status="$(curl --silent --show-error \
    -b "$COOKIE_JAR" \
    -o /dev/null \
    -w '%{http_code}' \
    -X DELETE \
    -H "X-PersonaLattice-CSRF: $FRESH_CSRF_TOKEN" \
    "$PUBLIC_URL/api/v1/cases/$case_id")"
  require_status 204 "$status" "retained case $case_id delete"
  status="$(curl --silent --show-error -b "$COOKIE_JAR" -o /dev/null -w '%{http_code}' "$PUBLIC_URL/api/v1/cases/$case_id")"
  require_status 404 "$status" "retained case $case_id post-delete"
done

LOGOUT_STATUS="$(curl --silent --show-error \
  -b "$COOKIE_JAR" \
  -o /dev/null \
  -w '%{http_code}' \
  -X POST \
  -H "X-PersonaLattice-CSRF: $FRESH_CSRF_TOKEN" \
  "$PUBLIC_URL/api/v1/auth/logout")"
require_status 204 "$LOGOUT_STATUS" "logout"
POST_LOGOUT_STATUS="$(curl --silent --show-error -b "$COOKIE_JAR" -o /dev/null -w '%{http_code}' "$PUBLIC_URL/api/v1/auth/session")"
require_status 401 "$POST_LOGOUT_STATUS" "revoked session"

stop_api
if [[ -n "$WEB_PID" ]]; then kill "$WEB_PID" 2>/dev/null || true; wait "$WEB_PID" 2>/dev/null || true; WEB_PID=""; fi
if [[ -n "$TUNNEL_PID" ]]; then kill "$TUNNEL_PID" 2>/dev/null || true; wait "$TUNNEL_PID" 2>/dev/null || true; TUNNEL_PID=""; fi

SENSITIVE_VALUES=(
  "$PERSONALATTICE_LC1_PASSWORD"
  "$PERSONALATTICE_ADMIN_PASSWORD_HASH"
  "$OLD_CSRF_TOKEN"
  "$FRESH_CSRF_TOKEN"
  "$OLD_SESSION_VALUE"
  "$FRESH_SESSION_VALUE"
  'PersonaLattice LC1 non-sensitive review fixture.'
  'private-converged-evidence-report-v1'
)
for key in BRAVE_SEARCH_API_KEY COMPANIES_HOUSE_API_KEY OPENALEX_API_KEY; do
  value=""
  case "$key" in
    BRAVE_SEARCH_API_KEY) value="${BRAVE_SEARCH_API_KEY:-}" ;;
    COMPANIES_HOUSE_API_KEY) value="${COMPANIES_HOUSE_API_KEY:-}" ;;
    OPENALEX_API_KEY) value="${OPENALEX_API_KEY:-}" ;;
  esac
  if [[ -n "$value" ]]; then SENSITIVE_VALUES+=("$value"); fi
done
for value in "${SENSITIVE_VALUES[@]}"; do
  [[ -z "$value" ]] && continue
  if grep -Fq -- "$value" "$API_LOG" "$WEB_LOG" "$TUNNEL_LOG"; then
    fail "sensitive/raw acceptance content appeared in process logs"
  fi
done

TESTED_COMMIT="$TESTED_COMMIT" PUBLIC_URL="$PUBLIC_URL" "$PYTHON" - "$EVIDENCE_PATH" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone

path = sys.argv[1]
payload = {
    "status": "passed",
    "completed_at": datetime.now(timezone.utc).isoformat(),
    "tested_commit": os.environ["TESTED_COMMIT"],
    "external_smoke_url": os.environ["PUBLIC_URL"],
    "test_identifiers": {
        "url": "https://github.com/octocat",
        "domain": "example.com",
        "reviewed_document": "non-sensitive generated fixture",
    },
    "verified": [
        "clean main fast-forwarded to origin/main",
        "detached isolated acceptance worktree",
        "production preflight",
        "clean Next.js production build",
        "loopback API and same-origin web proxy",
        "external HTTPS security headers",
        "external HTTPS admin auth and CSRF",
        "exact URL converged case",
        "domain converged case",
        "source-state/provenance/M5 response contracts",
        "reviewed-document preview-confirm-promote-explicit-run",
        "retained-case open/delete",
        "SQLite backup/restore",
        "process restart persistence",
        "old in-memory session invalidation",
        "logout revocation",
        "host-process log privacy scan",
    ],
    "still_requires_human_browser_acceptance": [
        "Safari rendered source-state/provenance/M5 inspection",
        "Chrome rendered source-state/provenance/M5 inspection",
        "responsive layout acceptance",
        "keyboard/focus acceptance",
    ],
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
os.chmod(path, 0o600)
PY

printf '\nLC1 automated host acceptance PASSED\n'
printf 'Tested commit: %s\n' "$TESTED_COMMIT"
printf 'Evidence: %s\n' "$EVIDENCE_PATH"
printf 'Remaining manual gate: Safari + Chrome rendered responsive/keyboard acceptance only.\n'
