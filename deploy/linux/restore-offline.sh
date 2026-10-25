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

# `is-active` returns 3 for an inactive service. Any other status, including
# active (0) or command/manager errors, must fail closed before restore.
IS_ACTIVE_EXIT=0
systemctl is-active --quiet persona-lattice.service 2>/dev/null || IS_ACTIVE_EXIT=$?
if [[ "$IS_ACTIVE_EXIT" -ne 3 ]]; then
  printf 'restore refused: service must be inactive (is-active exit %s; expected 3)\n' "$IS_ACTIVE_EXIT" >&2
  exit 1
fi

if ! LOAD_STATE="$(systemctl show --property=LoadState --value persona-lattice.service 2>/dev/null)"; then
  printf 'restore refused: cannot establish service load state\n' >&2
  exit 1
fi
if ! ACTIVE_STATE="$(systemctl show --property=ActiveState --value persona-lattice.service 2>/dev/null)"; then
  printf 'restore refused: cannot establish service activity state\n' >&2
  exit 1
fi
if [[ "$LOAD_STATE" != "loaded" || "$ACTIVE_STATE" != "inactive" ]]; then
  printf 'restore refused: persona-lattice.service must be loaded and inactive before restoring retained state\n' >&2
  exit 1
fi

exec bash "$ROOT/scripts/live_beta_restore.sh" "$BACKUP_PATH" --confirm-offline
