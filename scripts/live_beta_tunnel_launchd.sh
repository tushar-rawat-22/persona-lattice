#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TUNNEL_SCRIPT="$ROOT/scripts/live_beta_tunnel.sh"
LABEL="${PERSONALATTICE_TUNNEL_LAUNCHD_LABEL:-com.personalattice.private-beta-tunnel}"
PLIST_DIR="${PERSONALATTICE_LAUNCHD_PLIST_DIR:-$HOME/Library/LaunchAgents}"
PLIST="$PLIST_DIR/$LABEL.plist"
RUNTIME_DIR="${PERSONALATTICE_LIVE_RUNTIME_DIR:-$HOME/.local/share/persona-lattice/live}"
SERVICE_STDOUT="$RUNTIME_DIR/tunnel-launchd.stdout.log"
SERVICE_STDERR="$RUNTIME_DIR/tunnel-launchd.stderr.log"
SERVICE_PATH="${PERSONALATTICE_LAUNCHD_PATH:-$PATH}"
CONFIG="${PERSONALATTICE_CLOUDFLARED_CONFIG:-$HOME/.cloudflared/config.yml}"
PRIVATE_HOSTNAME="${PERSONALATTICE_PRIVATE_HOSTNAME:-}"
WEB_PORT="${PERSONALATTICE_LIVE_WEB_PORT:-13000}"
API_PORT="${PERSONALATTICE_LIVE_API_PORT:-18000}"
GUI_DOMAIN="gui/${UID:-$(id -u)}"

fail() {
  printf 'PersonaLattice tunnel launchd setup failed: %s\n' "$1" >&2
  exit 1
}

xml_escape() {
  printf '%s' "$1" | sed \
    -e 's/&/\&amp;/g' \
    -e 's/</\&lt;/g' \
    -e 's/>/\&gt;/g' \
    -e 's/"/\&quot;/g' \
    -e "s/'/\&apos;/g"
}

render_plist() {
  [[ -n "$PRIVATE_HOSTNAME" ]] || fail "PERSONALATTICE_PRIVATE_HOSTNAME is missing"

  local tunnel_escaped root_escaped path_escaped out_escaped err_escaped label_escaped
  local config_escaped hostname_escaped web_port_escaped api_port_escaped
  tunnel_escaped="$(xml_escape "$TUNNEL_SCRIPT")"
  root_escaped="$(xml_escape "$ROOT")"
  path_escaped="$(xml_escape "$SERVICE_PATH")"
  out_escaped="$(xml_escape "$SERVICE_STDOUT")"
  err_escaped="$(xml_escape "$SERVICE_STDERR")"
  label_escaped="$(xml_escape "$LABEL")"
  config_escaped="$(xml_escape "$CONFIG")"
  hostname_escaped="$(xml_escape "$PRIVATE_HOSTNAME")"
  web_port_escaped="$(xml_escape "$WEB_PORT")"
  api_port_escaped="$(xml_escape "$API_PORT")"

  cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label_escaped</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$tunnel_escaped</string>
    <string>run</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$root_escaped</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>$path_escaped</string>
    <key>PERSONALATTICE_CLOUDFLARED_CONFIG</key>
    <string>$config_escaped</string>
    <key>PERSONALATTICE_PRIVATE_HOSTNAME</key>
    <string>$hostname_escaped</string>
    <key>PERSONALATTICE_LIVE_WEB_PORT</key>
    <string>$web_port_escaped</string>
    <key>PERSONALATTICE_LIVE_API_PORT</key>
    <string>$api_port_escaped</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>
  <key>ThrottleInterval</key>
  <integer>10</integer>
  <key>ProcessType</key>
  <string>Background</string>
  <key>StandardOutPath</key>
  <string>$out_escaped</string>
  <key>StandardErrorPath</key>
  <string>$err_escaped</string>
</dict>
</plist>
EOF
}

require_macos() {
  [[ "$(uname -s)" == "Darwin" ]] || fail "install/uninstall/status require macOS launchd"
  command -v launchctl >/dev/null 2>&1 || fail "launchctl is unavailable"
}

install_service() {
  require_macos
  [[ -x "$TUNNEL_SCRIPT" ]] || fail "named-tunnel runner is not executable: $TUNNEL_SCRIPT"
  [[ -n "$PRIVATE_HOSTNAME" ]] || fail "PERSONALATTICE_PRIVATE_HOSTNAME is missing"

  PERSONALATTICE_CLOUDFLARED_CONFIG="$CONFIG" \
  PERSONALATTICE_PRIVATE_HOSTNAME="$PRIVATE_HOSTNAME" \
  PERSONALATTICE_LIVE_WEB_PORT="$WEB_PORT" \
  PERSONALATTICE_LIVE_API_PORT="$API_PORT" \
    "$TUNNEL_SCRIPT" preflight

  mkdir -p "$PLIST_DIR" "$RUNTIME_DIR"
  chmod 700 "$RUNTIME_DIR"

  local tmp="$PLIST.tmp.$$"
  umask 077
  render_plist >"$tmp"
  if command -v plutil >/dev/null 2>&1; then
    plutil -lint "$tmp" >/dev/null || {
      rm -f "$tmp"
      fail "generated tunnel launchd plist failed plutil validation"
    }
  fi
  mv "$tmp" "$PLIST"
  chmod 600 "$PLIST"

  launchctl bootout "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "$GUI_DOMAIN" "$PLIST"
  launchctl enable "$GUI_DOMAIN/$LABEL"
  launchctl kickstart -k "$GUI_DOMAIN/$LABEL"

  printf '%s\n' \
    "PersonaLattice private-beta tunnel launchd service installed." \
    "Label: $LABEL" \
    "Hostname: $PRIVATE_HOSTNAME" \
    "Plist: $PLIST" \
    "Runtime logs: $SERVICE_STDOUT and $SERVICE_STDERR" \
    "The plist stores routing metadata only; Cloudflare tunnel credentials remain in the owner-only credentials file referenced by cloudflared config."
}

uninstall_service() {
  require_macos
  launchctl bootout "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1 || true
  rm -f "$PLIST"
  printf 'PersonaLattice private-beta tunnel launchd service removed: %s\n' "$LABEL"
}

status_service() {
  require_macos
  launchctl print "$GUI_DOMAIN/$LABEL"
}

case "${1:-}" in
  render) render_plist ;;
  install) install_service ;;
  uninstall) uninstall_service ;;
  status) status_service ;;
  *) fail "usage: scripts/live_beta_tunnel_launchd.sh {render|install|uninstall|status}" ;;
esac
