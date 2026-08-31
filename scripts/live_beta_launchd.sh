#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_SCRIPT="$ROOT/scripts/live_beta_start.sh"
LABEL="${PERSONALATTICE_LAUNCHD_LABEL:-com.personalattice.private-beta}"
PLIST_DIR="${PERSONALATTICE_LAUNCHD_PLIST_DIR:-$HOME/Library/LaunchAgents}"
PLIST="$PLIST_DIR/$LABEL.plist"
RUNTIME_DIR="${PERSONALATTICE_LIVE_RUNTIME_DIR:-$HOME/.local/share/persona-lattice/live}"
SERVICE_STDOUT="$RUNTIME_DIR/launchd.stdout.log"
SERVICE_STDERR="$RUNTIME_DIR/launchd.stderr.log"
SERVICE_PATH="${PERSONALATTICE_LAUNCHD_PATH:-$PATH}"
GUI_DOMAIN="gui/${UID:-$(id -u)}"

fail() {
  printf 'PersonaLattice launchd setup failed: %s\n' "$1" >&2
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
  local start_escaped root_escaped path_escaped out_escaped err_escaped label_escaped
  start_escaped="$(xml_escape "$START_SCRIPT")"
  root_escaped="$(xml_escape "$ROOT")"
  path_escaped="$(xml_escape "$SERVICE_PATH")"
  out_escaped="$(xml_escape "$SERVICE_STDOUT")"
  err_escaped="$(xml_escape "$SERVICE_STDERR")"
  label_escaped="$(xml_escape "$LABEL")"

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
    <string>$start_escaped</string>
    <string>--run-prepared</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$root_escaped</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>$path_escaped</string>
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
  [[ -x "$START_SCRIPT" ]] || fail "private-beta runner is not executable: $START_SCRIPT"
  mkdir -p "$PLIST_DIR" "$RUNTIME_DIR"
  chmod 700 "$RUNTIME_DIR"

  "$START_SCRIPT" --prepare-only

  local tmp="$PLIST.tmp.$$"
  umask 077
  render_plist >"$tmp"
  if command -v plutil >/dev/null 2>&1; then
    plutil -lint "$tmp" >/dev/null || {
      rm -f "$tmp"
      fail "generated launchd plist failed plutil validation"
    }
  fi
  mv "$tmp" "$PLIST"
  chmod 600 "$PLIST"

  launchctl bootout "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "$GUI_DOMAIN" "$PLIST"
  launchctl enable "$GUI_DOMAIN/$LABEL"
  launchctl kickstart -k "$GUI_DOMAIN/$LABEL"

  printf '%s\n' \
    "PersonaLattice private-beta launchd service installed." \
    "Label: $LABEL" \
    "Plist: $PLIST" \
    "Runtime logs: $SERVICE_STDOUT and $SERVICE_STDERR" \
    "The service starts only the prepared loopback runtime; rerun install after changing the release."
}

uninstall_service() {
  require_macos
  launchctl bootout "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1 || true
  rm -f "$PLIST"
  printf 'PersonaLattice private-beta launchd service removed: %s\n' "$LABEL"
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
  *) fail "usage: scripts/live_beta_launchd.sh {render|install|uninstall|status}" ;;
esac
