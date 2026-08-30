#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/live_beta_start.sh"

[[ -f "$SCRIPT" ]]
bash -n "$SCRIPT"

require_text() {
  local needle="$1"
  grep -F -- "$needle" "$SCRIPT" >/dev/null || {
    printf 'live-beta runner contract missing: %s\n' "$needle" >&2
    exit 1
  }
}

require_text 'PERSONALATTICE_PRODUCTION_ENV_FILE'
require_text 'production environment file must be owner-only'
require_text 'PERSONALATTICE_COOKIE_SECURE must be true'
require_text 'PERSONALATTICE_SESSION_COOKIE must use the __Host- prefix'
require_text 'export PERSONALATTICE_API_ORIGIN="http://127.0.0.1:$API_PORT"'
require_text 'unset PERSONALATTICE_API_HOSTPORT'
require_text '"$PYTHON" -m app.launch_preflight'
require_text 'trap cleanup EXIT'
require_text "trap 'exit 130' INT"
require_text "trap 'exit 143' TERM"
require_text '--host 127.0.0.1'
require_text '--workers 1'
require_text '--no-proxy-headers'
require_text 'npm run build'
require_text 'npm run start -- --hostname 127.0.0.1'
require_text 'Publish only the web origin through the stable HTTPS ingress.'
require_text 'Do not expose the API port directly.'
require_text '--preflight-only'
require_text 'wait_for_runtime_failure()'
require_text 'jobs -pr'
require_text 'API process exited unexpectedly'
require_text 'web process exited unexpectedly'
require_text 'wait_for_runtime_failure'
require_text 'repository has uncommitted changes; private-beta releases require an exact clean commit'
require_text 'RELEASE_SHA="$(git -C "$ROOT" rev-parse HEAD)"'
require_text 'ROLLBACK_SHA="$(git -C "$ROOT" rev-parse HEAD^ 2>/dev/null)"'
require_text 'RELEASE_MANIFEST="$RUNTIME_DIR/release.env"'
require_text "printf 'release_sha=%s\\nrollback_sha=%s\\n' \"\$RELEASE_SHA\" \"\$ROLLBACK_SHA\""
require_text 'umask 077'
require_text 'mv "$MANIFEST_TMP" "$RELEASE_MANIFEST"'
require_text 'Release SHA: $RELEASE_SHA'
require_text 'Rollback SHA: $ROLLBACK_SHA'

manifest_line="$(grep -n -F 'mv "$MANIFEST_TMP" "$RELEASE_MANIFEST"' "$SCRIPT" | cut -d: -f1)"
web_health_line="$(grep -n -F 'wait_for_url "http://127.0.0.1:$WEB_PORT/api/health"' "$SCRIPT" | cut -d: -f1)"
if [[ -z "$manifest_line" || -z "$web_health_line" || "$manifest_line" -le "$web_health_line" ]]; then
  echo 'release manifest must be written only after API and web health checks pass' >&2
  exit 1
fi

if grep -F -- 'wait "$API_PID" "$WEB_PID"' "$SCRIPT" >/dev/null; then
  echo 'live-beta runner must fail closed when either child exits, not wait for both sequentially' >&2
  exit 1
fi
if grep -F -- 'cloudflared tunnel --url' "$SCRIPT" >/dev/null; then
  echo 'live-beta runner must not silently create a Quick Tunnel' >&2
  exit 1
fi
if grep -F -- 'npm run dev' "$SCRIPT" >/dev/null; then
  echo 'live-beta runner must use the production Next.js server, not dev mode' >&2
  exit 1
fi

printf 'live-beta start contract passed\n'
