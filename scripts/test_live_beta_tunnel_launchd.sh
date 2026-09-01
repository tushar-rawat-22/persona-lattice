#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/live_beta_tunnel_launchd.sh"
TUNNEL="$ROOT/scripts/live_beta_tunnel.sh"

[[ -f "$SCRIPT" ]]
[[ -f "$TUNNEL" ]]
bash -n "$SCRIPT"
bash -n "$TUNNEL"

require_text() {
  local file="$1"
  local needle="$2"
  grep -F -- "$needle" "$file" >/dev/null || {
    printf 'private-beta tunnel restart contract missing from %s: %s\n' "$file" "$needle" >&2
    exit 1
  }
}

require_text "$SCRIPT" '"$TUNNEL_SCRIPT" preflight'
require_text "$SCRIPT" '<string>run</string>'
require_text "$SCRIPT" '<key>RunAtLoad</key>'
require_text "$SCRIPT" '<key>KeepAlive</key>'
require_text "$SCRIPT" '<key>SuccessfulExit</key>'
require_text "$SCRIPT" 'launchctl bootstrap'
require_text "$SCRIPT" 'launchctl kickstart -k'
require_text "$SCRIPT" 'chmod 600 "$PLIST"'
require_text "$SCRIPT" 'Cloudflare tunnel credentials remain in the owner-only credentials file'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PERSONALATTICE_LAUNCHD_PLIST_DIR="$TMP/LaunchAgents" \
PERSONALATTICE_LIVE_RUNTIME_DIR="$TMP/runtime & logs" \
PERSONALATTICE_LAUNCHD_PATH='/opt/homebrew/bin:/usr/bin:/bin' \
PERSONALATTICE_CLOUDFLARED_CONFIG="$TMP/cloudflared & config.yml" \
PERSONALATTICE_PRIVATE_HOSTNAME='admin.example.test' \
PERSONALATTICE_LIVE_WEB_PORT='13000' \
PERSONALATTICE_LIVE_API_PORT='18000' \
  bash "$SCRIPT" render >"$TMP/tunnel-service.plist"

require_text "$TMP/tunnel-service.plist" '<string>com.personalattice.private-beta-tunnel</string>'
require_text "$TMP/tunnel-service.plist" '<string>/bin/bash</string>'
require_text "$TMP/tunnel-service.plist" '<string>run</string>'
require_text "$TMP/tunnel-service.plist" '<string>admin.example.test</string>'
require_text "$TMP/tunnel-service.plist" '<string>13000</string>'
require_text "$TMP/tunnel-service.plist" '<string>18000</string>'
require_text "$TMP/tunnel-service.plist" 'cloudflared &amp; config.yml'
require_text "$TMP/tunnel-service.plist" 'runtime &amp; logs/tunnel-launchd.stdout.log'

if grep -E 'credentials-file|PASSWORD_HASH|BRAVE_SEARCH_API_KEY|COMPANIES_HOUSE_API_KEY|TUNNEL_TOKEN' "$TMP/tunnel-service.plist" >/dev/null; then
  echo 'tunnel launchd plist must not contain credentials or application/provider secrets' >&2
  exit 1
fi

if grep -F -- 'trycloudflare.com' "$SCRIPT" >/dev/null || grep -F -- 'tunnel --url' "$SCRIPT" >/dev/null; then
  echo 'stable tunnel restart service must not create a Quick Tunnel' >&2
  exit 1
fi

printf 'live-beta tunnel launchd contract passed\n'
