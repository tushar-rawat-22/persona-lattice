#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT/services/api"
WEB_DIR="$ROOT/apps/web"
ENV_FILE="${PERSONALATTICE_PRODUCTION_ENV_FILE:-$HOME/.config/persona-lattice/production.env}"
RUNTIME_DIR="${PERSONALATTICE_LIVE_RUNTIME_DIR:-$HOME/.local/share/persona-lattice/live}"
VENV="${PERSONALATTICE_LIVE_VENV:-$RUNTIME_DIR/venv}"
API_PORT="${PERSONALATTICE_LIVE_API_PORT:-18000}"
WEB_PORT="${PERSONALATTICE_LIVE_WEB_PORT:-13000}"
API_LOG="$RUNTIME_DIR/api.log"
WEB_LOG="$RUNTIME_DIR/web.log"
RELEASE_MANIFEST="$RUNTIME_DIR/release.env"
API_PID=""
WEB_PID=""

fail() {
  printf 'PersonaLattice live-beta start failed: %s\n' "$1" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command '$1' is unavailable"
}

file_mode() {
  if stat -f '%Lp' "$1" >/dev/null 2>&1; then
    stat -f '%Lp' "$1"
  else
    stat -c '%a' "$1"
  fi
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

wait_for_runtime_failure() {
  while true; do
    local running_pids=()
    local pid
    while IFS= read -r pid; do
      [[ -n "$pid" ]] && running_pids+=("$pid")
    done < <(jobs -pr)

    local api_running=false
    local web_running=false
    for pid in "${running_pids[@]}"; do
      [[ "$pid" == "$API_PID" ]] && api_running=true
      [[ "$pid" == "$WEB_PID" ]] && web_running=true
    done

    if [[ "$api_running" != true ]]; then
      local api_status=0
      if wait "$API_PID"; then api_status=0; else api_status=$?; fi
      fail "API process exited unexpectedly (status $api_status); see $API_LOG"
    fi
    if [[ "$web_running" != true ]]; then
      local web_status=0
      if wait "$WEB_PID"; then web_status=0; else web_status=$?; fi
      fail "web process exited unexpectedly (status $web_status); see $WEB_LOG"
    fi
    sleep 1
  done
}

cleanup() {
  if [[ -n "$WEB_PID" ]]; then kill "$WEB_PID" 2>/dev/null || true; wait "$WEB_PID" 2>/dev/null || true; fi
  if [[ -n "$API_PID" ]]; then kill "$API_PID" 2>/dev/null || true; wait "$API_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

require_command curl
require_command git
require_command npm
require_command python3
require_command stat

[[ -f "$ENV_FILE" ]] || fail "production environment file not found: $ENV_FILE"
MODE="$(file_mode "$ENV_FILE")"
[[ "$MODE" == "600" || "$MODE" == "400" ]] || fail "production environment file must be owner-only (mode 600 or 400), got $MODE"

if ! git -C "$ROOT" diff --quiet -- || ! git -C "$ROOT" diff --cached --quiet --; then
  fail "repository has uncommitted changes; private-beta releases require an exact clean commit"
fi
RELEASE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
ROLLBACK_SHA="$(git -C "$ROOT" rev-parse HEAD^ 2>/dev/null)" || fail "current release has no rollback parent commit"

mkdir -p "$RUNTIME_DIR"
chmod 700 "$RUNTIME_DIR"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

[[ -n "${PERSONALATTICE_ADMIN_USERNAME:-}" ]] || fail "PERSONALATTICE_ADMIN_USERNAME is missing"
[[ -n "${PERSONALATTICE_ADMIN_PASSWORD_HASH:-}" ]] || fail "PERSONALATTICE_ADMIN_PASSWORD_HASH is missing"
[[ -n "${PERSONALATTICE_DB_PATH:-}" ]] || fail "PERSONALATTICE_DB_PATH is missing"
[[ "${PERSONALATTICE_COOKIE_SECURE:-}" == "true" ]] || fail "PERSONALATTICE_COOKIE_SECURE must be true"
[[ "${PERSONALATTICE_SESSION_COOKIE:-}" == __Host-* ]] || fail "PERSONALATTICE_SESSION_COOKIE must use the __Host- prefix"

if [[ ! -x "$VENV/bin/python" ]]; then
  python3 -m venv "$VENV"
fi
PYTHON="$VENV/bin/python"

"$PYTHON" -m pip install -q -e "$API_DIR"

export PERSONALATTICE_API_ORIGIN="http://127.0.0.1:$API_PORT"
unset PERSONALATTICE_API_HOSTPORT || true
"$PYTHON" -m app.launch_preflight >/dev/null

if [[ "${1:-}" == "--preflight-only" ]]; then
  printf 'PersonaLattice live-beta preflight passed.\n'
  exit 0
fi
[[ $# -eq 0 ]] || fail "usage: scripts/live_beta_start.sh [--preflight-only]"

(
  cd "$WEB_DIR"
  npm ci --no-audit --no-fund
  PERSONALATTICE_API_ORIGIN="$PERSONALATTICE_API_ORIGIN" npm run build
) >"$RUNTIME_DIR/build.log" 2>&1 || fail "web production build failed; see $RUNTIME_DIR/build.log"

(
  cd "$ROOT"
  exec "$PYTHON" -m uvicorn app.main:app \
    --app-dir services/api \
    --host 127.0.0.1 \
    --port "$API_PORT" \
    --workers 1 \
    --no-proxy-headers
) >"$API_LOG" 2>&1 &
API_PID=$!
wait_for_url "http://127.0.0.1:$API_PORT/health"

(
  cd "$WEB_DIR"
  PERSONALATTICE_API_ORIGIN="$PERSONALATTICE_API_ORIGIN" npm run start -- --hostname 127.0.0.1 --port "$WEB_PORT"
) >"$WEB_LOG" 2>&1 &
WEB_PID=$!
wait_for_url "http://127.0.0.1:$WEB_PORT/"
wait_for_url "http://127.0.0.1:$WEB_PORT/api/health"

umask 077
MANIFEST_TMP="$RELEASE_MANIFEST.tmp.$$"
printf 'release_sha=%s\nrollback_sha=%s\n' "$RELEASE_SHA" "$ROLLBACK_SHA" >"$MANIFEST_TMP"
mv "$MANIFEST_TMP" "$RELEASE_MANIFEST"

printf '%s\n' \
  "PersonaLattice private-beta processes are running on loopback." \
  "Release SHA: $RELEASE_SHA" \
  "Rollback SHA: $ROLLBACK_SHA" \
  "Release manifest: $RELEASE_MANIFEST" \
  "Web origin: http://127.0.0.1:$WEB_PORT" \
  "API origin: http://127.0.0.1:$API_PORT" \
  "Database:   $PERSONALATTICE_DB_PATH" \
  "" \
  "Publish only the web origin through the stable HTTPS ingress." \
  "Do not expose the API port directly." \
  "Press Control-C to stop the application processes."

wait_for_runtime_failure
