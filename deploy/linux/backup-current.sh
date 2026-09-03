#!/usr/bin/env bash
set -euo pipefail

ROOT="$(readlink -f /opt/persona-lattice/current)"
RELEASE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
STATE_ROOT="/var/lib/persona-lattice"

export PERSONALATTICE_PRODUCTION_ENV_FILE=/etc/persona-lattice/production.env
export PERSONALATTICE_BACKUP_DIR="$STATE_ROOT/backups"
export PERSONALATTICE_LIVE_RUNTIME_DIR="$STATE_ROOT/runtime/$RELEASE_SHA"
export PERSONALATTICE_RELEASE_MANIFEST="$PERSONALATTICE_LIVE_RUNTIME_DIR/release.env"

exec bash "$ROOT/scripts/live_beta_backup.sh"
