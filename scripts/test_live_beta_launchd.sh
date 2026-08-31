#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/live_beta_launchd.sh"
START="$ROOT/scripts/live_beta_start.sh"

[[ -f "$SCRIPT" ]]
[[ -f "$START" ]]
bash -n "$SCRIPT"
bash -n "$START"

require_text() {
  local file="$1"
  local needle="$2"
  grep -F -- "$needle" "$file" >/dev/null || {
    printf 'private-beta restart contract missing from %s: %s\n' "$file" "$needle" >&2
    exit 1
  }
}

require_text "$START" '--prepare-only'
require_text "$START" '--run-prepared'
require_text "$START" 'prepared Python environment is missing'
require_text "$START" 'prepared web production build is missing'
require_text "$SCRIPT" '"$START_SCRIPT" --prepare-only'
require_text "$SCRIPT" '<string>--run-prepared</string>'
require_text "$SCRIPT" '<key>RunAtLoad</key>'
require_text "$SCRIPT" '<key>KeepAlive</key>'
require_text "$SCRIPT" '<key>SuccessfulExit</key>'
require_text "$SCRIPT" 'launchctl bootstrap'
require_text "$SCRIPT" 'launchctl kickstart -k'
require_text "$SCRIPT" 'chmod 600 "$PLIST"'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PERSONALATTICE_LAUNCHD_PLIST_DIR="$TMP/LaunchAgents" \
PERSONALATTICE_LIVE_RUNTIME_DIR="$TMP/runtime & logs" \
PERSONALATTICE_LAUNCHD_PATH='/opt/homebrew/bin:/usr/bin:/bin' \
  bash "$SCRIPT" render >"$TMP/service.plist"

require_text "$TMP/service.plist" '<string>com.personalattice.private-beta</string>'
require_text "$TMP/service.plist" '<string>/bin/bash</string>'
require_text "$TMP/service.plist" '<string>--run-prepared</string>'
require_text "$TMP/service.plist" '<string>/opt/homebrew/bin:/usr/bin:/bin</string>'
require_text "$TMP/service.plist" 'runtime &amp; logs/launchd.stdout.log'

if grep -E 'PERSONALATTICE_ADMIN_PASSWORD|PASSWORD_HASH|BRAVE_SEARCH_API_KEY|COMPANIES_HOUSE_API_KEY' "$TMP/service.plist" >/dev/null; then
  echo 'launchd plist must not contain application/provider secrets' >&2
  exit 1
fi

if grep -F -- 'cloudflared tunnel --url' "$SCRIPT" >/dev/null; then
  echo 'restart service must not create a Quick Tunnel' >&2
  exit 1
fi

printf 'live-beta launchd contract passed\n'
