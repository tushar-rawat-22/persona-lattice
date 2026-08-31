#!/usr/bin/env bash
set -euo pipefail

CONFIG="${PERSONALATTICE_CLOUDFLARED_CONFIG:-$HOME/.cloudflared/config.yml}"
PRIVATE_HOSTNAME="${PERSONALATTICE_PRIVATE_HOSTNAME:-}"
WEB_PORT="${PERSONALATTICE_LIVE_WEB_PORT:-13000}"
API_PORT="${PERSONALATTICE_LIVE_API_PORT:-18000}"
MODE="${1:-preflight}"

fail() {
  printf 'PersonaLattice tunnel preflight failed: %s\n' "$1" >&2
  exit 1
}

file_mode() {
  if stat -f '%Lp' "$1" >/dev/null 2>&1; then
    stat -f '%Lp' "$1"
  else
    stat -c '%a' "$1"
  fi
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command '$1' is unavailable"
}

case "$MODE" in
  preflight|run) ;;
  *) fail "usage: scripts/live_beta_tunnel.sh [preflight|run]" ;;
esac

require_command cloudflared
require_command grep
require_command sed
require_command stat

[[ -n "$PRIVATE_HOSTNAME" ]] || fail "PERSONALATTICE_PRIVATE_HOSTNAME is missing"
[[ "$PRIVATE_HOSTNAME" =~ ^[A-Za-z0-9.-]+$ ]] || fail "PERSONALATTICE_PRIVATE_HOSTNAME must be a hostname without scheme, path or port"
[[ "$WEB_PORT" =~ ^[0-9]+$ ]] || fail "PERSONALATTICE_LIVE_WEB_PORT must be numeric"
[[ "$API_PORT" =~ ^[0-9]+$ ]] || fail "PERSONALATTICE_LIVE_API_PORT must be numeric"
[[ "$WEB_PORT" != "$API_PORT" ]] || fail "web and API ports must remain distinct"

[[ -f "$CONFIG" ]] || fail "cloudflared config not found: $CONFIG"

credentials_file="$(
  sed -n 's/^[[:space:]]*credentials-file:[[:space:]]*//p' "$CONFIG" \
    | head -n 1 \
    | sed -e 's/^[[:space:]"'\''']*//' -e 's/[[:space:]"'\''']*$//'
)"
[[ -n "$credentials_file" ]] || fail "cloudflared config must declare credentials-file"
[[ "$credentials_file" == /* ]] || fail "credentials-file must use an absolute path"
[[ -f "$credentials_file" ]] || fail "tunnel credentials file not found: $credentials_file"
credentials_mode="$(file_mode "$credentials_file")"
[[ "$credentials_mode" == "600" || "$credentials_mode" == "400" ]] || fail "tunnel credentials file must be owner-only (mode 600 or 400), got $credentials_mode"

if grep -E "^[[:space:]-]*service:[[:space:]]*https?://(127\\.0\\.0\\.1|localhost):${API_PORT}([/[:space:]]|$)" "$CONFIG" >/dev/null; then
  fail "cloudflared ingress must never target the private API port $API_PORT"
fi

cloudflared --config "$CONFIG" tunnel ingress validate >/dev/null

matched_rule="$(cloudflared --config "$CONFIG" tunnel ingress rule "https://$PRIVATE_HOSTNAME")"
expected_service="service: http://127.0.0.1:$WEB_PORT"
printf '%s\n' "$matched_rule" | grep -F -- "$expected_service" >/dev/null \
  || fail "private hostname must map exactly to $expected_service"

unmatched_rule="$(cloudflared --config "$CONFIG" tunnel ingress rule 'https://persona-lattice-unmatched.invalid')"
printf '%s\n' "$unmatched_rule" | grep -F -- 'service: http_status:404' >/dev/null \
  || fail "cloudflared ingress must end in a fail-closed 404 catch-all"

printf '%s\n' \
  "PersonaLattice named-tunnel preflight passed." \
  "Hostname: $PRIVATE_HOSTNAME" \
  "Origin:   http://127.0.0.1:$WEB_PORT" \
  "Config:   $CONFIG" \
  "API port $API_PORT is not published by this ingress contract."

if [[ "$MODE" == "run" ]]; then
  exec cloudflared --config "$CONFIG" tunnel run
fi
