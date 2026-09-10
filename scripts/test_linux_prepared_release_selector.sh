#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SELECTOR="$ROOT/deploy/linux/select-prepared-release.sh"
PREPARE="$ROOT/deploy/linux/prepare-release.sh"

fail() {
  printf 'Linux prepared-release selector contract failed: %s\n' "$1" >&2
  exit 1
}

bash -n "$SELECTOR" || fail "selector shell syntax failed"
bash -n "$PREPARE" || fail "prepare-release shell syntax failed"

require_literal() {
  local needle="$1" path="${2:-$SELECTOR}"
  grep -Fq -- "$needle" "$path" || fail "missing rollback contract in ${path#$ROOT/}: $needle"
}

forbid_literal() {
  local needle="$1"
  if grep -Fq -- "$needle" "$SELECTOR"; then
    fail "forbidden selector authority present: $needle"
  fi
}

require_literal '[[ "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]]'
require_literal 'TARGET_RELEASE="$RELEASE_ROOT/$TARGET_SHA"'
require_literal '[[ -d "$TARGET_RELEASE" && ! -L "$TARGET_RELEASE" ]]'
require_literal '[[ "$(readlink -f "$TARGET_RELEASE")" == "$TARGET_RELEASE" ]]'
require_literal '[[ "$(stat -c '\''%u'\'' "$TARGET_RELEASE")" == "0" ]]'
require_literal 'validate_retained_release_tree() {'
require_literal 'find "$release" -xdev ! -type l \( ! -user root -o -perm /022 \) -print -quit'
require_literal 'find "$release" -xdev -type l -print0'
require_literal 'readlink -f -- "$symlink"'
require_literal '[[ "$resolved" == "$release" || "$resolved" == "$release/"* ]]'
require_literal 'contains a broken retained symlink'
require_literal 'contains a retained symlink that escapes its release tree'
require_literal 'validate_retained_release_tree "$TARGET_RELEASE" "target prepared release"'
require_literal '[[ -f "$TARGET_UNIT" && ! -L "$TARGET_UNIT" ]]'

forbid_literal 'git fetch'
forbid_literal 'git clone'
forbid_literal 'npm ci'
forbid_literal 'pip install'
forbid_literal 'live_beta_start.sh --prepare-only'
forbid_literal 'prepare-release.sh'

require_literal '[[ -L "$CURRENT_LINK" && -d "$CURRENT_LINK" ]]'
require_literal '[[ "$PREVIOUS_RELEASE" == "$RELEASE_ROOT/$PREVIOUS_NAME" ]]'
require_literal '[[ "$PREVIOUS_NAME" =~ ^[0-9a-f]{40}$ ]]'
require_literal '[[ "$(stat -c '\''%u'\'' "$PREVIOUS_RELEASE")" == "0" ]]'
require_literal 'validate_retained_release_tree "$PREVIOUS_RELEASE" "current release"'
require_literal 'PREVIOUS_UNIT="$PREVIOUS_RELEASE/$UNIT_SOURCE"'
require_literal '[[ -f "$PREVIOUS_UNIT" && ! -L "$PREVIOUS_UNIT" ]]'
require_literal 'systemd unit target exists but is not a regular non-symlink file'
require_literal 'cmp -s -- "$UNIT_TARGET" "$PREVIOUS_UNIT"'
require_literal 'installed systemd unit does not match the current prepared release'

# Forward activation can restart the previous release after a failed deployment.
# It must apply the same retained-tree and installed-unit bindings before host mutation.
require_literal 'validate_retained_release_tree() {' "$PREPARE"
require_literal 'find "$release" -xdev ! -type l \( ! -user root -o -perm /022 \) -print -quit' "$PREPARE"
require_literal 'find "$release" -xdev -type l -print0' "$PREPARE"
require_literal 'readlink -f -- "$symlink"' "$PREPARE"
require_literal '[[ "$resolved" == "$release" || "$resolved" == "$release/"* ]]' "$PREPARE"
require_literal 'validate_retained_release_tree "$PREVIOUS_RELEASE" "current release"' "$PREPARE"
require_literal 'PREVIOUS_UNIT="$PREVIOUS_RELEASE/$UNIT_SOURCE"' "$PREPARE"
require_literal '[[ -f "$PREVIOUS_UNIT" && ! -L "$PREVIOUS_UNIT" ]]' "$PREPARE"
require_literal 'cmp -s -- "$UNIT_TARGET" "$PREVIOUS_UNIT"' "$PREPARE"
require_literal 'installed systemd unit does not match the current prepared release' "$PREPARE"

# Symlink mode bits must never be treated as ordinary writable-file authority.
# npm creates legitimate internal links such as node_modules/.bin/*; the scripts
# must instead reject broken links or links that resolve outside the exact release.
if grep -Fq -- 'find "$TARGET_RELEASE" -xdev \( ! -user root -o -perm /022 \)' "$SELECTOR"; then
  fail "selector still applies writable-mode checks directly to symlinks"
fi
if grep -Fq -- 'find "$PREVIOUS_RELEASE" -xdev \( ! -user root -o -perm /022 \)' "$PREPARE"; then
  fail "prepare-release still applies writable-mode checks directly to symlinks"
fi

require_literal 'install -d -m 0700 -o root -g root "$RUNTIME_ROOT"'
require_literal 'UNIT_BACKUP="$(mktemp "$RUNTIME_ROOT/select-unit.XXXXXX")"'
require_literal 'chmod 0600 "$UNIT_BACKUP"'
require_literal 'cp -- "$UNIT_TARGET" "$UNIT_BACKUP"'

require_literal 'systemctl is-enabled --quiet "$SERVICE_NAME"'
require_literal 'systemctl is-active --quiet "$SERVICE_NAME"'
require_literal 'ln -sfn "$TARGET_RELEASE" "$CURRENT_LINK"'
require_literal 'install -m 0644 "$TARGET_UNIT" "$UNIT_TARGET"'
require_literal 'systemctl daemon-reload'
require_literal 'http://127.0.0.1:18000/health'
require_literal 'http://127.0.0.1:13000/api/health'

require_literal 'restore_prior_state() {'
require_literal 'ln -sfn "$PREVIOUS_RELEASE" "$CURRENT_LINK" || failed=1'
require_literal 'install -m 0644 "$UNIT_BACKUP" "$UNIT_TARGET" || failed=1'
require_literal 'selected release failed health verification; prior host state was restored and verified'
require_literal 'manual recovery is required'

printf 'Linux prepared-release selector contract passed.\n'
