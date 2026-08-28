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
require_text 'python" -m app.launch_preflight'
require_text '--host 127.0.0.1'
require_text '--workers 1'
require_text '--no-proxy-headers'
require_text 'npm run build'
require_text 'npm run start -- --hostname 127.0.0.1'
require_text 'Publish only the web origin through the stable HTTPS ingress.'
require_text 'Do not expose the API port directly.'
require_text '--preflight-only'

if grep -F -- 'cloudflared tunnel --url' "$SCRIPT" >/dev/null; then
  echo 'live-beta runner must not silently create a Quick Tunnel' >&2
  exit 1
fi
if grep -F -- 'npm run dev' "$SCRIPT" >/dev/null; then
  echo 'live-beta runner must use the production Next.js server, not dev mode' >&2
  exit 1
fi

printf 'live-beta start contract passed\n'
