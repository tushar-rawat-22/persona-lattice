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

# Target code runs as the service identity during preparation and therefore can
# read production secrets. Fresh preparation must bind to the exact freshly
# fetched canonical main head, not merely any historical ancestor of main.
# Callers must also be unable to redefine the canonical repository.
require_literal 'REPOSITORY_URL="https://github.com/tushar-rawat-22/persona-lattice.git"' "$PREPARE"
require_literal 'git -C "$RELEASE_DIR" remote set-url origin "$REPOSITORY_URL"' "$PREPARE"
forbid_literal 'PERSONALATTICE_REPOSITORY_URL' "$PREPARE"
require_literal "git -C \"\$RELEASE_DIR\" fetch origin '+refs/heads/main:refs/remotes/origin/main'" "$PREPARE"
require_literal 'CANONICAL_MAIN_SHA="$(git -C "$RELEASE_DIR" rev-parse refs/remotes/origin/main)"' "$PREPARE"
require_literal '[[ "$TARGET_SHA" == "$CANONICAL_MAIN_SHA" ]]' "$PREPARE"
require_literal 'target release is not the current canonical origin/main head' "$PREPARE"
forbid_literal 'merge-base --is-ancestor "$TARGET_SHA" refs/remotes/origin/main' "$PREPARE"
forbid_literal 'target release is not an accepted commit in origin/main history' "$PREPARE"
forbid_literal 'git -C "$RELEASE_DIR" fetch --depth=1 origin "$TARGET_SHA"' "$PREPARE"
require_literal 'git -C "$RELEASE_DIR" checkout --detach --force "$TARGET_SHA"' "$PREPARE"

# Never trust persisted Git metadata from a prior preparation. The service
# identity temporarily owns the target checkout while dependencies/builds are
# prepared, so a later root invocation must discard any inactive target tree
# and clone it again from canonical origin. The currently selected release is
# never replaced in place.
require_literal 'if [[ -e "$RELEASE_DIR" || -L "$RELEASE_DIR" ]]; then' "$PREPARE"
require_literal 'target release is currently active; refusing in-place re-preparation' "$PREPARE"
require_literal 'rm -rf "$RELEASE_DIR"' "$PREPARE"
require_literal 'git clone --filter=blob:none --no-checkout "$REPOSITORY_URL" "$RELEASE_DIR"' "$PREPARE"

require_literal 'ENV_PERMISSION_HELPER="$RELEASE_DIR/scripts/live_beta_env_permissions.sh"' "$PREPARE"
require_literal 'target release environment-permission helper is missing' "$PREPARE"
require_literal 'runuser -u "$SERVICE_USER" -- bash -c' "$PREPARE"
require_literal 'source "$helper"' "$PREPARE"
require_literal 'personalattice_validate_env_file "$env_file"' "$PREPARE"
require_literal 'target release environment-permission validation failed' "$PREPARE"
forbid_literal 'source "$ENV_PERMISSION_HELPER"' "$PREPARE"
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

# Activation must be reversible as one unit. Refuse ambiguous current-release
# state before mutation; a real file/directory at /current makes ln -sfn create
# a nested link rather than select the requested release, while a broken link
# cannot provide a trustworthy rollback checkpoint.
require_literal 'if [[ -e "$CURRENT_LINK" && ! -L "$CURRENT_LINK" ]]; then' "$PREPARE"
require_literal 'current release path exists but is not a symlink' "$PREPARE"
require_literal 'if [[ -L "$CURRENT_LINK" && ! -d "$CURRENT_LINK" ]]; then' "$PREPARE"
require_literal 'current release symlink is broken or does not resolve to a directory' "$PREPARE"

# A resolving /current symlink is valid rollback state only when it identifies a
# root-owned SHA-named directory directly under the managed release root. This
# prevents a tampered symlink to an arbitrary directory from becoming trusted
# executable rollback authority after a failed activation.
require_literal 'PREVIOUS_RELEASE_NAME="${PREVIOUS_RELEASE##*/}"' "$PREPARE"
require_literal '[[ "$PREVIOUS_RELEASE" == "$RELEASE_ROOT/$PREVIOUS_RELEASE_NAME" ]]' "$PREPARE"
require_literal 'current release symlink resolves outside the managed release root' "$PREPARE"
require_literal '[[ "$PREVIOUS_RELEASE_NAME" =~ ^[0-9a-f]{40}$ ]]' "$PREPARE"
require_literal 'current release symlink does not resolve to a SHA-named release directory' "$PREPARE"
require_literal '[[ -d "$PREVIOUS_RELEASE" && ! -L "$PREVIOUS_RELEASE" ]]' "$PREPARE"
require_literal 'current release target is not a regular release directory' "$PREPARE"
require_literal '[[ "$(stat -c '\''%u'\'' "$PREVIOUS_RELEASE")" == "0" ]]' "$PREPARE"
require_literal 'current release target is not root-owned' "$PREPARE"

# The canonical systemd unit path is also root-controlled host authority. It
# must be absent or a regular file; a symlink/non-regular object could redirect
# install/rollback writes outside the intended release boundary.
require_literal 'if [[ -L "$UNIT_TARGET" || ( -e "$UNIT_TARGET" && ! -f "$UNIT_TARGET" ) ]]; then' "$PREPARE"
require_literal 'systemd unit target exists but is not a regular non-symlink file' "$PREPARE"

# A failed unit install/reload/start or a service that never becomes healthy
# must restore both the prior /current selection and the prior systemd unit.
# Recovery itself must then become healthy or fail loudly rather than claiming
# that rollback succeeded.
require_literal 'PREVIOUS_RELEASE="$(readlink -f "$CURRENT_LINK")"' "$PREPARE"
require_literal 'UNIT_BACKUP="$UNIT_TARGET.rollback.$$"' "$PREPARE"
require_literal 'systemctl is-enabled --quiet persona-lattice.service' "$PREPARE"
require_literal 'wait_for_release_health() {' "$PREPARE"
require_literal 'systemctl is-active --quiet persona-lattice.service' "$PREPARE"
require_literal 'http://127.0.0.1:18000/health' "$PREPARE"
require_literal 'http://127.0.0.1:13000/api/health' "$PREPARE"
require_literal '|| ! wait_for_release_health; then' "$PREPARE"
require_literal 'rollback_activation() {' "$PREPARE"
require_literal 'local rollback_failed=0' "$PREPARE"
require_literal 'ln -sfn "$PREVIOUS_RELEASE" "$CURRENT_LINK" || rollback_failed=1' "$PREPARE"
require_literal 'cp -p "$UNIT_BACKUP" "$UNIT_TARGET" || rollback_failed=1' "$PREPARE"
require_literal 'systemctl daemon-reload || rollback_failed=1' "$PREPARE"
require_literal 'if ! systemctl restart persona-lattice.service || ! wait_for_release_health; then' "$PREPARE"
require_literal 'systemctl disable persona-lattice.service >/dev/null 2>&1 || rollback_failed=1' "$PREPARE"
require_literal 'if ! rollback_activation; then' "$PREPARE"
require_literal 'release activation failed and rollback could not restore a healthy prior state; manual recovery is required' "$PREPARE"
require_literal 'release activation failed health verification; prior host state was restored and verified' "$PREPARE"
forbid_literal 'systemctl restart persona-lattice.service || true' "$PREPARE"

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
