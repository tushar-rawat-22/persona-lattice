#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT="$ROOT/deploy/linux/persona-lattice.service"
RUNNER="$ROOT/deploy/linux/run-current.sh"
PREPARE="$ROOT/deploy/linux/prepare-release.sh"
BACKUP="$ROOT/deploy/linux/backup-current.sh"
RESTORE="$ROOT/deploy/linux/restore-offline.sh"
VERIFY="$ROOT/deploy/linux/verify-host.sh"
ENV_EXAMPLE="$ROOT/deploy/linux/production.env.example"
TUNNEL="$ROOT/deploy/linux/cloudflared-config.yml.example"

fail() {
  printf 'Linux private-beta bundle contract failed: %s\n' "$1" >&2
  exit 1
}

for script in "$RUNNER" "$PREPARE" "$BACKUP" "$RESTORE" "$VERIFY"; do
  bash -n "$script" || fail "shell syntax failed: ${script#$ROOT/}"
done

require_literal() {
  local needle="$1" path="$2"
  grep -Fq -- "$needle" "$path" || fail "missing '$needle' in ${path#$ROOT/}"
}

forbid_literal() {
  local needle="$1" path="$2"
  if grep -Fq -- "$needle" "$path"; then
    fail "forbidden '$needle' present in ${path#$ROOT/}"
  fi
}

require_literal 'User=personalattice' "$UNIT"
require_literal 'Restart=on-failure' "$UNIT"
require_literal 'NoNewPrivileges=true' "$UNIT"
require_literal 'ExecStart=/usr/bin/bash /opt/persona-lattice/current/deploy/linux/run-current.sh' "$UNIT"
require_literal 'ReadWritePaths=/var/lib/persona-lattice' "$UNIT"
forbid_literal 'ReadWritePaths=/opt/persona-lattice' "$UNIT"

require_literal 'PERSONALATTICE_LIVE_API_PORT=18000' "$RUNNER"
require_literal 'PERSONALATTICE_LIVE_WEB_PORT=13000' "$RUNNER"
require_literal 'exec bash "$ROOT/scripts/live_beta_start.sh" --run-prepared' "$RUNNER"

require_literal 'PERSONALATTICE_DB_PATH=/var/lib/persona-lattice/data/personalattice.db' "$ENV_EXAMPLE"
require_literal 'PERSONALATTICE_COOKIE_SECURE=true' "$ENV_EXAMPLE"
require_literal 'PERSONALATTICE_SESSION_COOKIE=__Host-personalattice_session' "$ENV_EXAMPLE"

require_literal 'service: http://127.0.0.1:13000' "$TUNNEL"
forbid_literal 'service: http://127.0.0.1:18000' "$TUNNEL"
require_literal 'service: http_status:404' "$TUNNEL"

require_literal 'git -C "$RELEASE_DIR" checkout --detach --force "$TARGET_SHA"' "$PREPARE"
require_literal 'bash "$RELEASE_DIR/scripts/live_beta_start.sh" --prepare-only' "$PREPARE"
require_literal 'chown -R "root:$SERVICE_GROUP" "$RELEASE_DIR"' "$PREPARE"
require_literal 'chmod -R u=rwX,g=rX,o= "$RELEASE_DIR"' "$PREPARE"
require_literal 'systemctl restart persona-lattice.service' "$PREPARE"

require_literal 'exec bash "$ROOT/scripts/live_beta_backup.sh"' "$BACKUP"
require_literal 'systemctl is-active --quiet persona-lattice.service' "$RESTORE"
require_literal 'scripts/live_beta_restore.sh" "$BACKUP_PATH" --confirm-offline' "$RESTORE"
require_literal 'ss -H -ltn "sport = :$port"' "$VERIFY"
require_literal 'port $port is listening beyond loopback' "$VERIFY"

if grep -R -En '(PASSWORD_HASH=[^[:space:]]+|API_KEY=[^[:space:]]+)' "$ROOT/deploy/linux" --include='*.example' | grep -Ev '(PASSWORD_HASH=$|API_KEY=$)' >/dev/null; then
  fail "deployment examples appear to contain a credential value"
fi

printf 'Linux private-beta bundle contract passed.\n'
