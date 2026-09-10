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

[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "run as root"
[[ "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "usage: bash deploy/linux/prepare-release.sh <full-lowercase-git-sha>"

for command in git python3 node npm curl stat systemctl runuser install readlink getent groupadd useradd usermod chown chmod tr grep cp rm sleep mktemp; do
  command -v "$command" >/dev/null 2>&1 || fail "required command '$command' is unavailable"
done
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || fail "Python 3.11 or newer is required"

# Do not rely on distribution-specific useradd defaults to create a matching
# private group. The service group is part of the environment-file access
# boundary, so create it explicitly and ensure an existing service account is
# actually a member before handing it a root-owned 0640/0440 environment file.
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
# Preparation temporarily gives the service identity write access to the release
# checkout. If a previous preparation is interrupted, target code can therefore
# leave Git metadata behind. Never run root-owned Git commands through that
# persisted checkout on a later attempt. Reclone from canonical origin instead.
# Refuse to replace the currently selected release in place; rollback to another
# SHA remains safe because its release directory is not /current at that point.
if [[ -e "$RELEASE_DIR" || -L "$RELEASE_DIR" ]]; then
  if [[ -L "$CURRENT_LINK" && "$(readlink -f "$CURRENT_LINK")" == "$RELEASE_DIR" ]]; then
    fail "target release is currently active; refusing in-place re-preparation"
  fi
  rm -rf "$RELEASE_DIR"
fi
git clone --filter=blob:none --no-checkout "$REPOSITORY_URL" "$RELEASE_DIR"

# Target-owned preparation code executes as the service identity and can read
# production secrets. Fresh host preparation therefore requires current release
# authority, not merely historical membership in main. Fetch canonical main,
# resolve its exact head, and require the requested SHA to equal it before any
# target release code is checked out or executed. Historical prepared releases
# remain rollback state; they do not regain fresh preparation authority.
git -C "$RELEASE_DIR" remote set-url origin "$REPOSITORY_URL"
git -C "$RELEASE_DIR" fetch origin '+refs/heads/main:refs/remotes/origin/main'
CANONICAL_MAIN_SHA="$(git -C "$RELEASE_DIR" rev-parse refs/remotes/origin/main)"
[[ "$TARGET_SHA" == "$CANONICAL_MAIN_SHA" ]] \
  || fail "target release is not the current canonical origin/main head"

git -C "$RELEASE_DIR" checkout --detach --force "$TARGET_SHA"
[[ "$(git -C "$RELEASE_DIR" rev-parse HEAD)" == "$TARGET_SHA" ]] || fail "release checkout identity mismatch"
[[ -z "$(git -C "$RELEASE_DIR" status --porcelain)" ]] || fail "release checkout is not clean"

# Security policy must come from the exact target release, not from whichever
# checkout happened to invoke this bootstrap script. Validate that target-owned
# policy under the constrained service identity. The exact canonical-main check
# above is the authority boundary that makes target code eligible to run with
# access to the production environment.
ENV_PERMISSION_HELPER="$RELEASE_DIR/scripts/live_beta_env_permissions.sh"
[[ -f "$ENV_PERMISSION_HELPER" ]] || fail "target release environment-permission helper is missing: $ENV_PERMISSION_HELPER"
if ! runuser -u "$SERVICE_USER" -- bash -c '
  set -euo pipefail
  helper="$1"
  env_file="$2"
  # shellcheck disable=SC1090
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

# Preparation needs write access for the venv, node_modules and .next build. The
# release tree is sealed back to root ownership before the service can start.
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

# Activation is the only part that mutates the host's selected release. Refuse
# ambiguous/tampered host state before capturing rollback authority: /current is
# either absent or a resolving symlink managed by this installer, never a real
# file/directory where ln -sfn could create a nested link instead of selecting
# the requested release.
if [[ -e "$CURRENT_LINK" && ! -L "$CURRENT_LINK" ]]; then
  fail "current release path exists but is not a symlink: $CURRENT_LINK"
fi
if [[ -L "$CURRENT_LINK" && ! -d "$CURRENT_LINK" ]]; then
  fail "current release symlink is broken or does not resolve to a directory: $CURRENT_LINK"
fi

# A resolving symlink is still not sufficient rollback authority. It must point
# to one of our immutable, root-owned release directories and that directory name
# must itself be a full lowercase SHA. Otherwise a tampered /current path could
# be accepted as rollback state and later restarted with access to private-beta
# secrets after a failed activation.
PREVIOUS_RELEASE=""
if [[ -L "$CURRENT_LINK" ]]; then
  PREVIOUS_RELEASE="$(readlink -f "$CURRENT_LINK")"
  PREVIOUS_RELEASE_NAME="${PREVIOUS_RELEASE##*/}"
  [[ "$PREVIOUS_RELEASE" == "$RELEASE_ROOT/$PREVIOUS_RELEASE_NAME" ]] \
    || fail "current release symlink resolves outside the managed release root"
  [[ "$PREVIOUS_RELEASE_NAME" =~ ^[0-9a-f]{40}$ ]] \
    || fail "current release symlink does not resolve to a SHA-named release directory"
  [[ -d "$PREVIOUS_RELEASE" && ! -L "$PREVIOUS_RELEASE" ]] \
    || fail "current release target is not a regular release directory"
  [[ "$(stat -c '%u' "$PREVIOUS_RELEASE")" == "0" ]] \
    || fail "current release target is not root-owned"
fi

# The canonical unit path is root-controlled release state, not an extension
# point. Refuse symlinks and other non-regular objects before backup/install so
# a compromised or ambiguous host path cannot redirect a root write elsewhere.
if [[ -L "$UNIT_TARGET" || ( -e "$UNIT_TARGET" && ! -f "$UNIT_TARGET" ) ]]; then
  fail "systemd unit target exists but is not a regular non-symlink file: $UNIT_TARGET"
fi

# Keep a precise rollback checkpoint so a failed unit install/reload/restart
# cannot leave /current pointing at a release that never became runnable. The
# backup lives in a root-only runtime directory and mktemp creates it atomically;
# never derive a writable root destination from a predictable PID pathname next
# to the systemd unit.
UNIT_BACKUP=""
if [[ -f "$UNIT_TARGET" ]]; then
  UNIT_BACKUP="$(mktemp "$RELEASE_RUNTIME_ROOT/unit.XXXXXX")"
  chmod 0600 "$UNIT_BACKUP"
  cp -p -- "$UNIT_TARGET" "$UNIT_BACKUP"
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
    cp -p -- "$UNIT_BACKUP" "$UNIT_TARGET" || rollback_failed=1
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
