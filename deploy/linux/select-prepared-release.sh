#!/usr/bin/env bash
set -euo pipefail

TARGET_SHA="${1:-}"
SERVICE_NAME="persona-lattice.service"
RELEASE_ROOT="/opt/persona-lattice/releases"
CURRENT_LINK="/opt/persona-lattice/current"
UNIT_SOURCE="deploy/linux/persona-lattice.service"
UNIT_TARGET="/etc/systemd/system/persona-lattice.service"
RUNTIME_ROOT="/run/persona-lattice-release"

fail() {
  printf 'PersonaLattice prepared-release selection failed: %s\n' "$1" >&2
  exit 1
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "run as root"
[[ "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "usage: bash deploy/linux/select-prepared-release.sh <full-lowercase-git-sha>"

for command in stat systemctl install readlink chmod cp rm mktemp curl sleep ln find cmp; do
  command -v "$command" >/dev/null 2>&1 || fail "required command '$command' is unavailable"
done

TARGET_RELEASE="$RELEASE_ROOT/$TARGET_SHA"
TARGET_UNIT="$TARGET_RELEASE/$UNIT_SOURCE"

# Rollback reuses already prepared immutable state. It never fetches, clones,
# builds, or executes preparation code for a historical release.
[[ -d "$TARGET_RELEASE" && ! -L "$TARGET_RELEASE" ]] \
  || fail "target is not an existing prepared release directory"
[[ "$(readlink -f "$TARGET_RELEASE")" == "$TARGET_RELEASE" ]] \
  || fail "target release does not resolve directly under the managed release root"
[[ "$(stat -c '%u' "$TARGET_RELEASE")" == "0" ]] \
  || fail "target prepared release is not root-owned"
[[ -f "$TARGET_UNIT" && ! -L "$TARGET_UNIT" ]] \
  || fail "target prepared release systemd unit is missing or not a regular file"

# Older prepared releases are rollback authority only if the entire retained tree
# still satisfies the current immutability boundary. A root-owned top directory
# is insufficient when nested scripts or units could have been service-writable.
UNSAFE_TARGET_PATH="$(find "$TARGET_RELEASE" -xdev \( ! -user root -o -perm /022 \) -print -quit)"
[[ -z "$UNSAFE_TARGET_PATH" ]] \
  || fail "target prepared release contains non-root-owned or writable retained state"

# A bounded rollback needs trustworthy prior state so a failed selection can be
# reversed. Refuse manual/tampered host state instead of guessing.
[[ -L "$CURRENT_LINK" && -d "$CURRENT_LINK" ]] \
  || fail "current release is not a resolving managed symlink"
PREVIOUS_RELEASE="$(readlink -f "$CURRENT_LINK")"
PREVIOUS_NAME="${PREVIOUS_RELEASE##*/}"
PREVIOUS_UNIT="$PREVIOUS_RELEASE/$UNIT_SOURCE"
[[ "$PREVIOUS_RELEASE" == "$RELEASE_ROOT/$PREVIOUS_NAME" ]] \
  || fail "current release resolves outside the managed release root"
[[ "$PREVIOUS_NAME" =~ ^[0-9a-f]{40}$ ]] \
  || fail "current release is not SHA-named"
[[ -d "$PREVIOUS_RELEASE" && ! -L "$PREVIOUS_RELEASE" ]] \
  || fail "current release target is not a regular release directory"
[[ "$(stat -c '%u' "$PREVIOUS_RELEASE")" == "0" ]] \
  || fail "current release target is not root-owned"
UNSAFE_PREVIOUS_PATH="$(find "$PREVIOUS_RELEASE" -xdev \( ! -user root -o -perm /022 \) -print -quit)"
[[ -z "$UNSAFE_PREVIOUS_PATH" ]] \
  || fail "current release contains non-root-owned or writable retained state"
[[ -f "$PREVIOUS_UNIT" && ! -L "$PREVIOUS_UNIT" ]] \
  || fail "current release systemd unit is missing or not a regular file"

if [[ -L "$UNIT_TARGET" || ( -e "$UNIT_TARGET" && ! -f "$UNIT_TARGET" ) ]]; then
  fail "systemd unit target exists but is not a regular non-symlink file"
fi
[[ -f "$UNIT_TARGET" ]] || fail "current systemd unit is missing; repair host state before selecting a rollback release"
cmp -s -- "$UNIT_TARGET" "$PREVIOUS_UNIT" \
  || fail "installed systemd unit does not match the current prepared release; repair host state before selecting a rollback release"

if [[ "$PREVIOUS_RELEASE" == "$TARGET_RELEASE" ]]; then
  printf 'PersonaLattice prepared release already selected: %s\n' "$TARGET_SHA"
  exit 0
fi

install -d -m 0700 -o root -g root "$RUNTIME_ROOT"
UNIT_BACKUP="$(mktemp "$RUNTIME_ROOT/select-unit.XXXXXX")"
chmod 0600 "$UNIT_BACKUP"
cp -- "$UNIT_TARGET" "$UNIT_BACKUP"

WAS_ENABLED=0
WAS_ACTIVE=0
if systemctl is-enabled --quiet "$SERVICE_NAME" >/dev/null 2>&1; then
  WAS_ENABLED=1
fi
if systemctl is-active --quiet "$SERVICE_NAME" >/dev/null 2>&1; then
  WAS_ACTIVE=1
fi

wait_for_release_health() {
  local attempt
  for ((attempt=1; attempt<=40; attempt++)); do
    if systemctl is-active --quiet "$SERVICE_NAME" \
      && curl --silent --show-error --fail --max-time 3 http://127.0.0.1:18000/health >/dev/null 2>&1 \
      && curl --silent --show-error --fail --max-time 3 http://127.0.0.1:13000/api/health >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

restore_prior_state() {
  local failed=0
  ln -sfn "$PREVIOUS_RELEASE" "$CURRENT_LINK" || failed=1
  install -m 0644 "$UNIT_BACKUP" "$UNIT_TARGET" || failed=1
  systemctl daemon-reload || failed=1

  if [[ "$WAS_ENABLED" -eq 1 ]]; then
    systemctl enable "$SERVICE_NAME" >/dev/null || failed=1
  else
    systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || failed=1
  fi

  if [[ "$WAS_ACTIVE" -eq 1 ]]; then
    if ! systemctl restart "$SERVICE_NAME" || ! wait_for_release_health; then
      failed=1
    fi
  else
    systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || failed=1
  fi

  rm -f "$UNIT_BACKUP" || failed=1
  [[ "$failed" -eq 0 ]]
}

# Preserve the prior enabled/running authority. Selecting a prepared rollback is
# not permission to turn on a service that was intentionally disabled or stopped.
if ! ln -sfn "$TARGET_RELEASE" "$CURRENT_LINK" \
  || ! install -m 0644 "$TARGET_UNIT" "$UNIT_TARGET" \
  || ! systemctl daemon-reload; then
  if ! restore_prior_state; then
    fail "rollback selection failed and prior host state could not be restored; manual recovery is required"
  fi
  fail "rollback selection failed before service activation; prior host state was restored"
fi

if [[ "$WAS_ENABLED" -eq 1 ]]; then
  if ! systemctl enable "$SERVICE_NAME" >/dev/null; then
    if ! restore_prior_state; then
      fail "rollback selection failed and prior host state could not be restored; manual recovery is required"
    fi
    fail "rollback selection could not preserve enabled state; prior host state was restored"
  fi
else
  systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || {
    if ! restore_prior_state; then
      fail "rollback selection failed and prior host state could not be restored; manual recovery is required"
    fi
    fail "rollback selection could not preserve disabled state; prior host state was restored"
  }
fi

if [[ "$WAS_ACTIVE" -eq 1 ]]; then
  if ! systemctl restart "$SERVICE_NAME" || ! wait_for_release_health; then
    if ! restore_prior_state; then
      fail "selected release failed health verification and prior host state could not be restored; manual recovery is required"
    fi
    fail "selected release failed health verification; prior host state was restored and verified"
  fi
else
  if ! systemctl stop "$SERVICE_NAME" >/dev/null 2>&1; then
    if ! restore_prior_state; then
      fail "rollback selection failed and prior host state could not be restored; manual recovery is required"
    fi
    fail "rollback selection could not preserve stopped state; prior host state was restored"
  fi
fi

rm -f "$UNIT_BACKUP"
printf '%s\n' \
  "PersonaLattice prepared release selected." \
  "Release: $TARGET_SHA" \
  "Previous release: $PREVIOUS_NAME" \
  "Service enabled before selection: $WAS_ENABLED" \
  "Service active before selection: $WAS_ACTIVE"
