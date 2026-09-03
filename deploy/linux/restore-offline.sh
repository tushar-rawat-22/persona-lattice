#!/usr/bin/env bash
set -euo pipefail

BACKUP_PATH="${1:-}"
[[ -n "$BACKUP_PATH" ]] || {
  printf 'usage: sudo -u personalattice bash deploy/linux/restore-offline.sh BACKUP.sqlite3\n' >&2
  exit 2
}

ROOT="$(readlink -f /opt/persona-lattice/current)"
export PERSONALATTICE_PRODUCTION_ENV_FILE=/etc/persona-lattice/production.env
export PERSONALATTICE_BACKUP_DIR=/var/lib/persona-lattice/backups

if systemctl is-active --quiet persona-lattice.service 2>/dev/null; then
  printf 'restore refused: stop persona-lattice.service before restoring retained state\n' >&2
  exit 1
fi

exec bash "$ROOT/scripts/live_beta_restore.sh" "$BACKUP_PATH" --confirm-offline
