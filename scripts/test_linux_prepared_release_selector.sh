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
require_literal 'UNSAFE_TARGET_PATH="$(find "$TARGET_RELEASE" -xdev \( ! -user root -o -perm /022 \) -print -quit)"'
require_literal 'target prepared release contains non-root-owned or writable retained state'
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
require_literal 'UNSAFE_PREVIOUS_PATH="$(find "$PREVIOUS_RELEASE" -xdev \( ! -user root -o -perm /022 \) -print -quit)"'
require_literal 'current release contains non-root-owned or writable retained state'
require_literal 'systemd unit target exists but is not a regular non-symlink file'

# Forward activation can restart the previous release after a failed deployment.
# It must apply the same recursive retained-tree boundary before host mutation.
require_literal 'UNSAFE_PREVIOUS_PATH="$(find "$PREVIOUS_RELEASE" -xdev \( ! -user root -o -perm /022 \) -print -quit)"' "$PREPARE"
require_literal 'current release contains non-root-owned or writable retained state' "$PREPARE"

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
