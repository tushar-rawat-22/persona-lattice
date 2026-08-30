#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PERSONALATTICE_PRODUCTION_ENV_FILE:-$HOME/.config/persona-lattice/production.env}"
BACKUP_DIR="${PERSONALATTICE_BACKUP_DIR:-$HOME/.local/share/persona-lattice/backups}"

fail() {
  printf 'PersonaLattice live-beta backup failed: %s\n' "$1" >&2
  exit 1
}

file_mode() {
  if stat -f '%Lp' "$1" >/dev/null 2>&1; then
    stat -f '%Lp' "$1"
  else
    stat -c '%a' "$1"
  fi
}

command -v python3 >/dev/null 2>&1 || fail "required command 'python3' is unavailable"
command -v stat >/dev/null 2>&1 || fail "required command 'stat' is unavailable"

[[ -f "$ENV_FILE" ]] || fail "production environment file not found: $ENV_FILE"
MODE="$(file_mode "$ENV_FILE")"
[[ "$MODE" == "600" || "$MODE" == "400" ]] || fail "production environment file must be owner-only (mode 600 or 400), got $MODE"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

[[ -n "${PERSONALATTICE_DB_PATH:-}" ]] || fail "PERSONALATTICE_DB_PATH is missing"
[[ "$PERSONALATTICE_DB_PATH" == /* ]] || fail "PERSONALATTICE_DB_PATH must be absolute"
[[ -f "$PERSONALATTICE_DB_PATH" ]] || fail "database file not found: $PERSONALATTICE_DB_PATH"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
umask 077

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_PATH="$BACKUP_DIR/persona-lattice-$TIMESTAMP.sqlite3"
TEMP_PATH="$BACKUP_PATH.tmp.$$"
RESTORE_CHECK="$BACKUP_DIR/.restore-check-$TIMESTAMP-$$.sqlite3"
trap 'rm -f "$TEMP_PATH" "$RESTORE_CHECK"' EXIT

python3 - "$PERSONALATTICE_DB_PATH" "$TEMP_PATH" "$RESTORE_CHECK" <<'PY'
import hashlib
import os
import sqlite3
import sys

source_path, backup_path, restore_check_path = sys.argv[1:]

source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
backup = sqlite3.connect(backup_path)
try:
    source.backup(backup)
finally:
    backup.close()
    source.close()

check = sqlite3.connect(backup_path)
try:
    result = check.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        raise SystemExit(f"backup integrity_check failed: {result!r}")
finally:
    check.close()

source_backup = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
restored = sqlite3.connect(restore_check_path)
try:
    source_backup.backup(restored)
finally:
    restored.close()
    source_backup.close()

check = sqlite3.connect(restore_check_path)
try:
    result = check.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        raise SystemExit(f"restore-check integrity_check failed: {result!r}")
finally:
    check.close()

with open(backup_path, "rb") as handle:
    digest = hashlib.sha256(handle.read()).hexdigest()
print(digest)
PY

DIGEST="$(python3 - "$TEMP_PATH" <<'PY'
import hashlib
import sys
with open(sys.argv[1], "rb") as handle:
    print(hashlib.sha256(handle.read()).hexdigest())
PY
)"

mv "$TEMP_PATH" "$BACKUP_PATH"
rm -f "$RESTORE_CHECK"
trap - EXIT

printf '%s\n' \
  "PersonaLattice live-beta SQLite backup passed." \
  "Database: $PERSONALATTICE_DB_PATH" \
  "Backup: $BACKUP_PATH" \
  "SHA256: $DIGEST" \
  "Integrity: ok" \
  "Restore check: ok"
