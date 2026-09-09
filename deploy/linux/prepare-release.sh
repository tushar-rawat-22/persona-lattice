#!/usr/bin/env bash
set -euo pipefail

TARGET_SHA="${1:-}"
REPOSITORY_URL="${PERSONALATTICE_REPOSITORY_URL:-https://github.com/tushar-rawat-22/persona-lattice.git}"
SERVICE_USER="personalattice"
SERVICE_GROUP="personalattice"
RELEASE_ROOT="/opt/persona-lattice/releases"
CURRENT_LINK="/opt/persona-lattice/current"
STATE_ROOT="/var/lib/persona-lattice"
ENV_FILE="/etc/persona-lattice/production.env"
UNIT_SOURCE="deploy/linux/persona-lattice.service"
UNIT_TARGET="/etc/systemd/system/persona-lattice.service"

fail() {
  printf 'PersonaLattice Linux release preparation failed: %s\n' "$1" >&2
  exit 1
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "run as root"
[[ "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "usage: bash deploy/linux/prepare-release.sh <full-lowercase-git-sha>"

for command in git python3 node npm curl stat systemctl runuser install readlink getent groupadd useradd usermod chown chmod tr grep; do
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

RELEASE_DIR="$RELEASE_ROOT/$TARGET_SHA"
if [[ ! -d "$RELEASE_DIR/.git" ]]; then
  rm -rf "$RELEASE_DIR"
  git clone --filter=blob:none --no-checkout "$REPOSITORY_URL" "$RELEASE_DIR"
fi

git -C "$RELEASE_DIR" fetch --depth=1 origin "$TARGET_SHA"
git -C "$RELEASE_DIR" checkout --detach --force "$TARGET_SHA"
[[ "$(git -C "$RELEASE_DIR" rev-parse HEAD)" == "$TARGET_SHA" ]] || fail "release checkout identity mismatch"
[[ -z "$(git -C "$RELEASE_DIR" status --porcelain)" ]] || fail "release checkout is not clean"

# Security policy must come from the exact target release, not from whichever
# checkout happened to invoke this bootstrap script. That keeps upgrades and
# rollbacks self-contained and prevents stale local policy from qualifying a
# different release SHA.
ENV_PERMISSION_HELPER="$RELEASE_DIR/scripts/live_beta_env_permissions.sh"
[[ -f "$ENV_PERMISSION_HELPER" ]] || fail "target release environment-permission helper is missing: $ENV_PERMISSION_HELPER"
# shellcheck disable=SC1090
source "$ENV_PERMISSION_HELPER"
if ! personalattice_validate_env_file "$ENV_FILE"; then
  fail "$personalattice_env_permissions_error"
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
ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"
install -m 0644 "$RELEASE_DIR/$UNIT_SOURCE" "$UNIT_TARGET"
systemctl daemon-reload
systemctl enable persona-lattice.service >/dev/null
systemctl restart persona-lattice.service

printf '%s\n' \
  "PersonaLattice Linux private-beta release prepared and started." \
  "Release SHA: $TARGET_SHA" \
  "Current release: $CURRENT_LINK -> $RELEASE_DIR" \
  "Persistent SQLite directory: $STATE_ROOT/data" \
  "API: loopback 127.0.0.1:18000 only" \
  "Web: loopback 127.0.0.1:13000 only" \
  "Rollback: rerun this script with the previous full release SHA."
