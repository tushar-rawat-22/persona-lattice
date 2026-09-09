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
ENV_PERMISSION_HELPER="$ROOT/scripts/live_beta_env_permissions.sh"
LIVE_START="$ROOT/scripts/live_beta_start.sh"
LIVE_BACKUP="$ROOT/scripts/live_beta_backup.sh"

fail() {
  printf 'Linux private-beta bundle contract failed: %s\n' "$1" >&2
  exit 1
}

for script in "$RUNNER" "$PREPARE" "$BACKUP" "$RESTORE" "$VERIFY" "$ENV_PERMISSION_HELPER" "$LIVE_START" "$LIVE_BACKUP"; do
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

# Exercise the permission policy itself, rather than only grepping deployment
# scripts. Local owner-only files remain valid; Linux group readability is valid
# only for the root-owned service-group handoff created by prepare-release.sh.
# shellcheck disable=SC1090
source "$ENV_PERMISSION_HELPER"
assert_env_metadata_pass() {
  personalattice_validate_env_metadata "$1" "$2" "$3" || \
    fail "expected env metadata to pass: mode=$1 owner=$2 group=$3 ($personalattice_env_permissions_error)"
}
assert_env_metadata_fail() {
  if personalattice_validate_env_metadata "$1" "$2" "$3"; then
    fail "expected env metadata to fail: mode=$1 owner=$2 group=$3"
  fi
}
assert_env_metadata_pass 600 analyst staff
assert_env_metadata_pass 400 analyst staff
assert_env_metadata_pass 640 root personalattice
assert_env_metadata_pass 440 root personalattice
assert_env_metadata_fail 640 analyst personalattice
assert_env_metadata_fail 640 root root
assert_env_metadata_fail 440 personalattice personalattice
assert_env_metadata_fail 644 root personalattice

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
require_literal 'ENV_PERMISSION_HELPER="$RELEASE_DIR/scripts/live_beta_env_permissions.sh"' "$PREPARE"
require_literal 'target release environment-permission helper is missing' "$PREPARE"
require_literal 'source "$ENV_PERMISSION_HELPER"' "$PREPARE"
require_literal 'personalattice_validate_env_file "$ENV_FILE"' "$PREPARE"
require_literal 'bash "$RELEASE_DIR/scripts/live_beta_start.sh" --prepare-only' "$PREPARE"
require_literal 'chown -R "root:$SERVICE_GROUP" "$RELEASE_DIR"' "$PREPARE"
require_literal 'chmod -R u=rwX,g=rX,o= "$RELEASE_DIR"' "$PREPARE"
require_literal 'chown "root:$SERVICE_GROUP" "$ENV_FILE"' "$PREPARE"
require_literal '600|640) chmod 0640 "$ENV_FILE" ;;' "$PREPARE"
require_literal '400|440) chmod 0440 "$ENV_FILE" ;;' "$PREPARE"
forbid_literal 'ENV_PERMISSION_HELPER="$ROOT/scripts/live_beta_env_permissions.sh"' "$PREPARE"
forbid_literal 'environment file must be mode 600 or 400 before preparation' "$PREPARE"
forbid_literal 'chown "$SERVICE_USER:$SERVICE_GROUP" "$ENV_FILE"' "$PREPARE"
require_literal 'groupadd --system "$SERVICE_GROUP"' "$PREPARE"
require_literal 'useradd --system --gid "$SERVICE_GROUP"' "$PREPARE"
require_literal 'usermod --append --groups "$SERVICE_GROUP" "$SERVICE_USER"' "$PREPARE"

# Activation must be reversible as one unit. A failed unit install/reload/start
# must restore both the prior /current selection and the prior systemd unit.
require_literal 'PREVIOUS_RELEASE="$(readlink -f "$CURRENT_LINK")"' "$PREPARE"
require_literal 'UNIT_BACKUP="$UNIT_TARGET.rollback.$$"' "$PREPARE"
require_literal 'systemctl is-enabled --quiet persona-lattice.service' "$PREPARE"
require_literal 'rollback_activation() {' "$PREPARE"
require_literal 'ln -sfn "$PREVIOUS_RELEASE" "$CURRENT_LINK"' "$PREPARE"
require_literal 'cp -p "$UNIT_BACKUP" "$UNIT_TARGET"' "$PREPARE"
require_literal 'systemctl disable persona-lattice.service' "$PREPARE"
require_literal 'release activation failed; previous release selection was restored' "$PREPARE"
require_literal 'systemctl restart persona-lattice.service' "$PREPARE"

require_literal 'source "$ENV_PERMISSION_HELPER"' "$LIVE_START"
require_literal 'personalattice_validate_env_file "$ENV_FILE"' "$LIVE_START"
require_literal 'source "$ENV_PERMISSION_HELPER"' "$LIVE_BACKUP"
require_literal 'personalattice_validate_env_file "$ENV_FILE"' "$LIVE_BACKUP"

require_literal 'exec bash "$ROOT/scripts/live_beta_backup.sh"' "$BACKUP"
require_literal 'systemctl is-active --quiet persona-lattice.service' "$RESTORE"
require_literal 'scripts/live_beta_restore.sh" "$BACKUP_PATH" --confirm-offline' "$RESTORE"
require_literal 'ss -H -ltn "sport = :$port"' "$VERIFY"
require_literal 'port $port is listening beyond loopback' "$VERIFY"

if grep -R -En '(PASSWORD_HASH=[^[:space:]]+|API_KEY=[^[:space:]]+)' "$ROOT/deploy/linux" --include='*.example' | grep -Ev '(PASSWORD_HASH=$|API_KEY=$)' >/dev/null; then
  fail "deployment examples appear to contain a credential value"
fi

printf 'Linux private-beta bundle contract passed.\n'
