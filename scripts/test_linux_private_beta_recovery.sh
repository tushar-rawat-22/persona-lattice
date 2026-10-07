#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREPARE="$ROOT/deploy/linux/prepare-release.sh"
SELECTOR="$ROOT/deploy/linux/select-prepared-release.sh"
ENV_HELPER="$ROOT/scripts/live_beta_env_permissions.sh"
LIVE_START="$ROOT/scripts/live_beta_start.sh"
LIVE_BACKUP="$ROOT/scripts/live_beta_backup.sh"
LIVE_RESTORE="$ROOT/scripts/live_beta_restore.sh"

fail() {
  printf 'Linux private-beta recovery contract failed: %s\n' "$1" >&2
  exit 1
}

for script in "$PREPARE" "$SELECTOR" "$ENV_HELPER" "$LIVE_START" "$LIVE_BACKUP" "$LIVE_RESTORE"; do
  [[ -f "$script" ]] || fail "missing ${script#$ROOT/}"
  bash -n "$script" || fail "shell syntax failed: ${script#$ROOT/}"
done

require_literal() {
  local needle="$1" path="$2"
  grep -Fq -- "$needle" "$path" || fail "missing contract in ${path#$ROOT/}: $needle"
}

forbid_literal() {
  local needle="$1" path="$2"
  if grep -Fq -- "$needle" "$path"; then
    fail "forbidden authority in ${path#$ROOT/}: $needle"
  fi
}

# Local single-owner config stays valid. The Linux service may read production
# config only through a root-owned, service-group-readable handoff; it must not
# own or be able to rewrite the config containing secrets.
# shellcheck disable=SC1090
source "$ENV_HELPER"
personalattice_validate_env_metadata 600 analyst staff || fail "owner-only local config was rejected"
personalattice_validate_env_metadata 400 analyst staff || fail "read-only local config was rejected"
personalattice_validate_env_metadata 640 root personalattice || fail "root-owned Linux config was rejected"
personalattice_validate_env_metadata 440 root personalattice || fail "root-owned read-only Linux config was rejected"
for metadata in \
  '640 analyst personalattice' \
  '640 root root' \
  '440 personalattice personalattice' \
  '644 root personalattice'; do
  # shellcheck disable=SC2086
  if personalattice_validate_env_metadata $metadata; then
    fail "unsafe config metadata was accepted: $metadata"
  fi
done

for script in "$LIVE_START" "$LIVE_BACKUP" "$LIVE_RESTORE"; do
  require_literal 'source "$ENV_PERMISSION_HELPER"' "$script"
  require_literal 'personalattice_validate_env_file "$ENV_FILE"' "$script"
done
require_literal 'chown "root:$SERVICE_GROUP" "$ENV_FILE"' "$PREPARE"
require_literal '600|640) chmod 0640 "$ENV_FILE" ;;' "$PREPARE"
require_literal '400|440) chmod 0440 "$ENV_FILE" ;;' "$PREPARE"
forbid_literal 'chown "$SERVICE_USER:$SERVICE_GROUP" "$ENV_FILE"' "$PREPARE"

# New preparation is exact-current-main only. Historical rollback selects only
# an already prepared release and has no network, package-install, or build
# authority.
require_literal 'REPOSITORY_URL="https://github.com/tushar-rawat-22/persona-lattice.git"' "$PREPARE"
forbid_literal 'PERSONALATTICE_REPOSITORY_URL' "$PREPARE"
require_literal "git -C \"\$RELEASE_DIR\" fetch origin '+refs/heads/main:refs/remotes/origin/main'" "$PREPARE"
require_literal 'CANONICAL_MAIN_SHA="$(git -C "$RELEASE_DIR" rev-parse refs/remotes/origin/main)"' "$PREPARE"
require_literal '[[ "$TARGET_SHA" == "$CANONICAL_MAIN_SHA" ]]' "$PREPARE"

require_literal 'TARGET_RELEASE="$RELEASE_ROOT/$TARGET_SHA"' "$SELECTOR"
require_literal '[[ -d "$TARGET_RELEASE" && ! -L "$TARGET_RELEASE" ]]' "$SELECTOR"
require_literal '[[ "$(readlink -f "$TARGET_RELEASE")" == "$TARGET_RELEASE" ]]' "$SELECTOR"
require_literal '[[ "$(stat -c '\''%u'\'' "$TARGET_RELEASE")" == "0" ]]' "$SELECTOR"
for forbidden in 'git fetch' 'git clone' 'npm ci' 'pip install' 'live_beta_start.sh --prepare-only' 'prepare-release.sh'; do
  forbid_literal "$forbidden" "$SELECTOR"
done

# Retained release trees must be root-owned and not group/world writable.
# npm-created internal symlinks remain valid, but broken or escaping symlinks
# are rejected before either forward activation or rollback mutates host state.
for script in "$PREPARE" "$SELECTOR"; do
  require_literal 'validate_retained_release_tree() {' "$script"
  require_literal 'find "$release" -xdev ! -type l \( ! -user root -o -perm /022 \) -print -quit' "$script"
  require_literal 'find "$release" -xdev -type l -print0' "$script"
  require_literal 'readlink -f -- "$symlink"' "$script"
  require_literal '[[ "$resolved" == "$release" || "$resolved" == "$release/"* ]]' "$script"
  require_literal 'contains a broken retained symlink' "$script"
  require_literal 'contains a retained symlink that escapes its release tree' "$script"
done

require_literal 'validate_retained_release_tree "$TARGET_RELEASE" "target prepared release"' "$SELECTOR"
require_literal 'validate_retained_release_tree "$PREVIOUS_RELEASE" "current release"' "$SELECTOR"
require_literal 'validate_retained_release_tree "$RELEASE_DIR" "newly prepared release"' "$PREPARE"
require_literal 'validate_retained_release_tree "$PREVIOUS_RELEASE" "current release"' "$PREPARE"
require_literal '[[ -f "$RELEASE_DIR/$UNIT_SOURCE" && ! -L "$RELEASE_DIR/$UNIT_SOURCE" ]]' "$PREPARE"

# Activation and retained rollback are failure-atomic across /current, the
# installed unit, service state, and live API/web health.
for script in "$PREPARE" "$SELECTOR"; do
  require_literal 'cmp -s -- "$UNIT_TARGET" "$PREVIOUS_UNIT"' "$script"
  require_literal 'systemctl is-enabled --quiet' "$script"
  require_literal 'systemctl is-active --quiet' "$script"
  require_literal 'http://127.0.0.1:18000/health' "$script"
  require_literal 'http://127.0.0.1:13000/api/health' "$script"
  require_literal 'manual recovery is required' "$script"
done

require_literal 'rollback_activation() {' "$PREPARE"
require_literal 'ln -sfn "$PREVIOUS_RELEASE" "$CURRENT_LINK" || rollback_failed=1' "$PREPARE"
require_literal 'install -m 0644 "$UNIT_BACKUP" "$UNIT_TARGET" || rollback_failed=1' "$PREPARE"
require_literal 'restore_prior_state() {' "$SELECTOR"
require_literal 'ln -sfn "$PREVIOUS_RELEASE" "$CURRENT_LINK" || failed=1' "$SELECTOR"
require_literal 'install -m 0644 "$UNIT_BACKUP" "$UNIT_TARGET" || failed=1' "$SELECTOR"

printf 'Linux private-beta recovery contract passed.\n'
