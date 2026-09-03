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

for command in git python3 npm curl stat systemctl runuser install readlink; do
  command -v "$command" >/dev/null 2>&1 || fail "required command '$command' is unavailable"
done

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --home-dir "$STATE_ROOT" --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

install -d -m 0755 -o root -g root /opt/persona-lattice "$RELEASE_ROOT"
install -d -m 0700 -o "$SERVICE_USER" -g "$SERVICE_GROUP" \
  "$STATE_ROOT" "$STATE_ROOT/data" "$STATE_ROOT/backups" "$STATE_ROOT/runtime"
install -d -m 0750 -o root -g "$SERVICE_GROUP" /etc/persona-lattice

[[ -f "$ENV_FILE" ]] || fail "owner-only environment file is missing: $ENV_FILE (copy deploy/linux/production.env.example and fill secrets first)"
ENV_MODE="$(stat -c '%a' "$ENV_FILE")"
[[ "$ENV_MODE" == "600" || "$ENV_MODE" == "400" ]] || fail "environment file must be mode 600 or 400, got $ENV_MODE"
chown "$SERVICE_USER:$SERVICE_GROUP" "$ENV_FILE"

RELEASE_DIR="$RELEASE_ROOT/$TARGET_SHA"
if [[ ! -d "$RELEASE_DIR/.git" ]]; then
  rm -rf "$RELEASE_DIR"
  git clone --filter=blob:none --no-checkout "$REPOSITORY_URL" "$RELEASE_DIR"
fi

git -C "$RELEASE_DIR" fetch --depth=1 origin "$TARGET_SHA"
git -C "$RELEASE_DIR" checkout --detach --force "$TARGET_SHA"
[[ "$(git -C "$RELEASE_DIR" rev-parse HEAD)" == "$TARGET_SHA" ]] || fail "release checkout identity mismatch"
[[ -z "$(git -C "$RELEASE_DIR" status --porcelain)" ]] || fail "release checkout is not clean"
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
