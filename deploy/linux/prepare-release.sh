#!/usr/bin/env bash
set -euo pipefail

TARGET_SHA="${1:-}"
REPOSITORY_URL="https://github.com/tushar-rawat-22/persona-lattice.git"
SERVICE_USER="personalattice"
SERVICE_GROUP="personalattice"
RELEASE_ROOT="/opt/persona-lattice/releases"
CURRENT_LINK="/opt/persona-lattice/current"
STATE_ROOT="/var/lib/persona-lattice"
ENV_FILE="/etc/persona-lattice/production.env"
UNIT_SOURCE="deploy/linux/persona-lattice.service"
UNIT_TARGET="/etc/systemd/system/persona-lattice.service"
RELEASE_RUNTIME_ROOT="/run/persona-lattice-release"

fail() {
  printf 'PersonaLattice Linux release preparation failed: %s\n' "$1" >&2
  exit 1
}

validate_retained_release_tree() {
  local release="$1" label="$2" unsafe_path symlink resolved

  unsafe_path="$(find "$release" -xdev ! -type l \( ! -user root -o -perm /022 \) -print -quit)"
  [[ -z "$unsafe_path" ]] \
    || fail "$label contains non-root-owned or writable retained state: $unsafe_path"

  while IFS= read -r -d '' symlink; do
    if ! resolved="$(readlink -f -- "$symlink")"; then
      fail "$label contains a broken retained symlink: $symlink"
    fi
    [[ "$resolved" == "$release" || "$resolved" == "$release/"* ]] \
      || fail "$label contains a retained symlink that escapes its release tree: $symlink"
  done < <(find "$release" -xdev -type l -print0)
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "run as root"
[[ "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "usage: bash deploy/linux/prepare-release.sh <full-lowercase-git-sha>"

for command in git python3 node npm curl stat systemctl runuser install readlink getent groupadd useradd usermod chown chmod tr grep cp rm sleep mktemp find cmp; do
  command -v "$command" >/dev/null 2>&1 || fail "required command '$command' is unavailable"
done
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || fail "Python 3.11 or newer is required"

if ! getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
  groupadd --system "$SERVICE_GROUP"
fi
if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --gid "$SERVICE_GROUP" --home-dir "$STATE_ROOT" --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
elif ! id -nG "$SERVICE_USER" | tr ' ' '\n' | grep -Fxq "$SERVICE_GROUP"; then
  usermod --append --groups "$SERVICE_GROUP" "$SERVICE_USER"
fi

install -d -m 0755 -o root -g root /opt/persona-lattice "$RELEASE_ROOT"
install -d -m 0700 -o "$SERVICE_USER" -g "$SERVICE_GROUP" \
  "$STATE_ROOT" "$STATE_ROOT/data" "$STATE_ROOT/backups" "$STATE_ROOT/runtime"
install -d -m 0750 -o root -g "$SERVICE_GROUP" /etc/persona-lattice
install -d -m 0700 -o root -g root "$RELEASE_RUNTIME_ROOT"

RELEASE_DIR="$RELEASE_ROOT/$TARGET_SHA"
if [[ -e "$RELEASE_DIR" || -L "$RELEASE_DIR" ]]; then
  if [[ -L "$CURRENT_LINK" && "$(readlink -f "$CURRENT_LINK")" == "$RELEASE_DIR" ]]; then
    fail "target release is currently active; refusing in-place re-preparation"
  fi
  rm -rf "$RELEASE_DIR"
fi
git clone --filter=blob:none --no-checkout "$REPOSITORY_URL" "$RELEASE_DIR"

git -C "$RELEASE_DIR" remote set-url origin "$REPOSITORY_URL"
git -C "$RELEASE_DIR" fetch origin '+refs/heads/main:refs/remotes/origin/main'
CANONICAL_MAIN_SHA="$(git -C "$RELEASE_DIR" rev-parse refs/remotes/origin/main)"
[[ "$TARGET_SHA" == "$CANONICAL_MAIN_SHA" ]] \
  || fail "target release is not the current canonical origin/main head"

git -C "$RELEASE_DIR" checkout --detach --force "$TARGET_SHA"
[[ "$(git -C "$RELEASE_DIR" rev-parse HEAD)" == "$TARGET_SHA" ]] || fail "release checkout identity mismatch"
[[ -z "$(git -C "$RELEASE_DIR" status --porcelain)" ]] || fail "release checkout is not clean"

ENV_PERMISSION_HELPER="$RELEASE_DIR/scripts/live_beta_env_permissions.sh"
[[ -f "$ENV_PERMISSION_HELPER" ]] || fail "target release environment-permission helper is missing: $ENV_PERMISSION_HELPER"
if ! runuser -u "$SERVICE_USER" -- bash -c '
  set -euo pipefail
  helper="$1"
  env_file="$2"
  source "$helper"
  if ! personalattice_validate_env_file "$env_file"; then
    printf "%s\n" "$personalattice_env_permissions_error" >&2
    exit 1
  fi
' -- "$ENV_PERMISSION_HELPER" "$ENV_FILE"; then
  fail "target release environment-permission validation failed"
fi
ENV_MODE="$(stat -c '%a' "$ENV_FILE")"
chown "root:$SERVICE_GROUP" "$ENV_FILE"
case "$ENV_MODE" in
  600|640) chmod 0640 "$ENV_FILE" ;;
  400|440) chmod 0440 "$ENV_FILE" ;;
  *) fail "validated environment file has unexpected mode $ENV_MODE" ;;
esac

EXPECTED_NODE_MAJOR="$(tr -d '[:space:]' <"$RELEASE_DIR/.nvmrc")"
ACTUAL_NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[[ "$ACTUAL_NODE_MAJOR" == "$EXPECTED_NODE_MAJOR" ]] || fail "Node $EXPECTED_NODE_MAJOR.x is required by the release; found $(node --version)"

chown -R "$SERVICE_USER:$SERVICE_GROUP" "$RELEASE_DIR"
RUNTIME_DIR="$STATE_ROOT/runtime/$TARGET_SHA"
install -d -m 0700 -o "$SERVICE_USER" -g "$SERVICE_GROUP" "$RUNTIME_DIR"

runuser -u "$SERVICE_USER" -- env \
  PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" \
  PERSONALATTICE_LIVE_RUNTIME_DIR="$RUNTIME_DIR" \
  PERSONALATTICE_LIVE_VENV="$RUNTIME_DIR/venv" \
  PERSONALATTICE_LIVE_API_PORT=18000 \
  PERSONALATTICE_LIVE_WEB_PORT=13000 \
  bash "$RELEASE_DIR/scripts/live_beta_start.sh" --prepare-only

chown -R "root:$SERVICE_GROUP" "$RELEASE_DIR"
chmod -R u=rwX,g=rX,o= "$RELEASE_DIR"

if [[ -e "$CURRENT_LINK" && ! -L "$CURRENT_LINK" ]]; then
  fail "current release path exists but is not a symlink: $CURRENT_LINK"
fi
if [[ -L "$CURRENT_LINK" && ! -d "$CURRENT_LINK" ]]; then
  fail "current release symlink is broken or does not resolve to a directory: $CURRENT_LINK"
fi

PREVIOUS_RELEASE=""
PREVIOUS_UNIT=""
if [[ -L "$CURRENT_LINK" ]]; then
  PREVIOUS_RELEASE="$(readlink -f "$CURRENT_LINK")"
  PREVIOUS_RELEASE_NAME="${PREVIOUS_RELEASE##*/}"
  PREVIOUS_UNIT="$PREVIOUS_RELEASE/$UNIT_SOURCE"
  [[ "$PREVIOUS_RELEASE" == "$RELEASE_ROOT/$PREVIOUS_RELEASE_NAME" ]] \
    || fail "current release symlink resolves outside the managed release root"
  [[ "$PREVIOUS_RELEASE_NAME" =~ ^[0-9a-f]{40}$ ]] \
    || fail "current release symlink does not resolve to a SHA-named release directory"
  [[ -d "$PREVIOUS_RELEASE" && ! -L "$PREVIOUS_RELEASE" ]] \
    || fail "current release target is not a regular release directory"
  [[ "$(stat -c '%u' "$PREVIOUS_RELEASE")" == "0" ]] \
    || fail "current release target is not root-owned"
  validate_retained_release_tree "$PREVIOUS_RELEASE" "current release"
  [[ -f "$PREVIOUS_UNIT" && ! -L "$PREVIOUS_UNIT" ]] \
    || fail "current release systemd unit is missing or not a regular file"
fi

if [[ -L "$UNIT_TARGET" || ( -e "$UNIT_TARGET" && ! -f "$UNIT_TARGET" ) ]]; then
  fail "systemd unit target exists but is not a regular non-symlink file: $UNIT_TARGET"
fi
if [[ -n "$PREVIOUS_RELEASE" ]]; then
  [[ -f "$UNIT_TARGET" ]] \
    || fail "installed systemd unit is missing for the current prepared release"
  cmp -s -- "$UNIT_TARGET" "$PREVIOUS_UNIT" \
    || fail "installed systemd unit does not match the current prepared release; repair host state before preparing another release"
fi

UNIT_BACKUP=""
if [[ -f "$UNIT_TARGET" ]]; then
  UNIT_BACKUP="$(mktemp "$RELEASE_RUNTIME_ROOT/unit.XXXXXX")"
  chmod 0600 "$UNIT_BACKUP"
  cp -- "$UNIT_TARGET" "$UNIT_BACKUP"
fi
WAS_ENABLED=0
if systemctl is-enabled --quiet persona-lattice.service >/dev/null 2>&1; then
  WAS_ENABLED=1
fi

wait_for_release_health() {
  local attempt
  for ((attempt=1; attempt<=40; attempt++)); do
    if systemctl is-active --quiet persona-lattice.service \
      && curl --silent --show-error --fail --max-time 3 http://127.0.0.1:18000/health >/dev/null 2>&1 \
      && curl --silent --show-error --fail --max-time 3 http://127.0.0.1:13000/api/health >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

rollback_activation() {
  local rollback_failed=0

  if [[ -n "$PREVIOUS_RELEASE" ]]; then
    ln -sfn "$PREVIOUS_RELEASE" "$CURRENT_LINK" || rollback_failed=1
  else
    rm -f "$CURRENT_LINK" || rollback_failed=1
  fi
  if [[ -n "$UNIT_BACKUP" && -f "$UNIT_BACKUP" ]]; then
    install -m 0644 "$UNIT_BACKUP" "$UNIT_TARGET" || rollback_failed=1
  else
    rm -f "$UNIT_TARGET" || rollback_failed=1
  fi
  systemctl daemon-reload || rollback_failed=1

  if [[ "$rollback_failed" -eq 0 && "$WAS_ENABLED" -eq 1 && -n "$PREVIOUS_RELEASE" ]]; then
    if ! systemctl restart persona-lattice.service || ! wait_for_release_health; then
      rollback_failed=1
    fi
  else
    systemctl stop persona-lattice.service >/dev/null 2>&1 || rollback_failed=1
    systemctl disable persona-lattice.service >/dev/null 2>&1 || rollback_failed=1
  fi

  [[ -z "$UNIT_BACKUP" ]] || rm -f "$UNIT_BACKUP" || rollback_failed=1
  [[ "$rollback_failed" -eq 0 ]]
}

if ! ln -sfn "$RELEASE_DIR" "$CURRENT_LINK" \
  || ! install -m 0644 "$RELEASE_DIR/$UNIT_SOURCE" "$UNIT_TARGET" \
  || ! systemctl daemon-reload \
  || ! systemctl enable persona-lattice.service >/dev/null \
  || ! systemctl restart persona-lattice.service \
  || ! wait_for_release_health; then
  if ! rollback_activation; then
    fail "release activation failed and rollback could not restore a healthy prior state; manual recovery is required"
  fi
  fail "release activation failed health verification; prior host state was restored and verified"
fi
[[ -z "$UNIT_BACKUP" ]] || rm -f "$UNIT_BACKUP"

printf '%s\n' \
  "PersonaLattice Linux private-beta release prepared and started." \
  "Release SHA: $TARGET_SHA" \
  "Current release: $CURRENT_LINK -> $RELEASE_DIR" \
  "Persistent SQLite directory: $STATE_ROOT/data" \
  "API: loopback 127.0.0.1:18000 only" \
  "Web: loopback 127.0.0.1:13000 only" \
  "Rollback: select a previously prepared, root-owned release through the recovery procedure; do not re-prepare historical code."
