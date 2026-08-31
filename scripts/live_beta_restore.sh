#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${PERSONALATTICE_PRODUCTION_ENV_FILE:-$HOME/.config/persona-lattice/production.env}"
BACKUP_DIR="${PERSONALATTICE_BACKUP_DIR:-$HOME/.local/share/persona-lattice/backups}"

fail() {
  printf 'PersonaLattice live-beta restore failed: %s\n' "$1" >&2
  exit 1
}

file_mode() {
  if stat -f '%Lp' "$1" >/dev/null 2>&1; then stat -f '%Lp' "$1"; else stat -c '%a' "$1"; fi
}

sha256_file() {
  python3 - "$1" <<'PY'
import hashlib, sys
with open(sys.argv[1], "rb") as handle:
    print(hashlib.sha256(handle.read()).hexdigest())
PY
}

[[ $# -eq 2 && "$2" == "--confirm-offline" ]] || fail "usage: scripts/live_beta_restore.sh BACKUP.sqlite3 --confirm-offline"
BACKUP_PATH="$1"
EVIDENCE_PATH="$BACKUP_PATH.env"

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
[[ -f "$BACKUP_PATH" ]] || fail "backup file not found: $BACKUP_PATH"
[[ -f "$EVIDENCE_PATH" ]] || fail "backup evidence file not found: $EVIDENCE_PATH"
BACKUP_MODE="$(file_mode "$BACKUP_PATH")"
EVIDENCE_MODE="$(file_mode "$EVIDENCE_PATH")"
[[ "$BACKUP_MODE" == "600" || "$BACKUP_MODE" == "400" ]] || fail "backup file must be owner-only (mode 600 or 400), got $BACKUP_MODE"
[[ "$EVIDENCE_MODE" == "600" || "$EVIDENCE_MODE" == "400" ]] || fail "backup evidence file must be owner-only (mode 600 or 400), got $EVIDENCE_MODE"

readarray -t EVIDENCE_VALUES < <(python3 - "$EVIDENCE_PATH" <<'PY'
import re
import sys

path = sys.argv[1]
allowed = {"backup_sha256", "release_sha", "rollback_sha"}
values = {}
with open(path, encoding="utf-8") as handle:
    for raw_line in handle:
        line = raw_line.strip()
        if not line:
            continue
        key, separator, value = line.partition("=")
        if separator != "=" or key not in allowed:
            continue
        if key in values:
            raise SystemExit(f"duplicate {key} in backup evidence")
        values[key] = value
if re.fullmatch(r"[0-9a-f]{64}", values.get("backup_sha256", "")) is None:
    raise SystemExit("invalid backup_sha256 in backup evidence")
for key in ("release_sha", "rollback_sha"):
    value = values.get(key, "")
    if value != "unavailable" and re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise SystemExit(f"invalid {key} in backup evidence")
print(values["backup_sha256"])
print(values.get("release_sha", "unavailable"))
print(values.get("rollback_sha", "unavailable"))
PY
) || fail "backup evidence could not be parsed safely: $EVIDENCE_PATH"
EXPECTED_DIGEST="${EVIDENCE_VALUES[0]}"
RELEASE_SHA="${EVIDENCE_VALUES[1]}"
ROLLBACK_SHA="${EVIDENCE_VALUES[2]}"
ACTUAL_DIGEST="$(sha256_file "$BACKUP_PATH")"
[[ "$ACTUAL_DIGEST" == "$EXPECTED_DIGEST" ]] || fail "backup digest does not match evidence"

python3 - "$BACKUP_PATH" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
try:
    result = conn.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        raise SystemExit(f"backup integrity_check failed: {result!r}")
finally:
    conn.close()
PY

DB_DIR="$(dirname "$PERSONALATTICE_DB_PATH")"
mkdir -p "$DB_DIR" "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
umask 077
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TEMP_RESTORE="$DB_DIR/.persona-lattice-restore-$TIMESTAMP-$$.sqlite3"
SAFETY_BACKUP="$BACKUP_DIR/pre-restore-$TIMESTAMP.sqlite3"
RESTORE_EVIDENCE="$BACKUP_DIR/restore-$TIMESTAMP.env"
RESTORE_EVIDENCE_TEMP="$RESTORE_EVIDENCE.tmp.$$"
trap 'rm -f "$TEMP_RESTORE" "$RESTORE_EVIDENCE_TEMP"' EXIT

if [[ -f "$PERSONALATTICE_DB_PATH" ]]; then
  python3 - "$PERSONALATTICE_DB_PATH" "$SAFETY_BACKUP" <<'PY'
import sqlite3, sys
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
try:
    source.backup(target)
finally:
    target.close(); source.close()
PY
  chmod 600 "$SAFETY_BACKUP"
fi

python3 - "$BACKUP_PATH" "$TEMP_RESTORE" <<'PY'
import sqlite3, sys
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
try:
    source.backup(target)
finally:
    target.close(); source.close()
check = sqlite3.connect(sys.argv[2])
try:
    result = check.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        raise SystemExit(f"restored database integrity_check failed: {result!r}")
finally:
    check.close()
PY
chmod 600 "$TEMP_RESTORE"
mv "$TEMP_RESTORE" "$PERSONALATTICE_DB_PATH"
chmod 600 "$PERSONALATTICE_DB_PATH"
RESTORED_DIGEST="$(sha256_file "$PERSONALATTICE_DB_PATH")"

printf 'restored_from=%s\nbackup_sha256=%s\nrestored_sha256=%s\nrelease_sha=%s\nrollback_sha=%s\nsafety_backup=%s\n' \
  "$BACKUP_PATH" "$EXPECTED_DIGEST" "$RESTORED_DIGEST" "$RELEASE_SHA" "$ROLLBACK_SHA" \
  "${SAFETY_BACKUP:-unavailable}" >"$RESTORE_EVIDENCE_TEMP"
chmod 600 "$RESTORE_EVIDENCE_TEMP"
mv "$RESTORE_EVIDENCE_TEMP" "$RESTORE_EVIDENCE"
trap - EXIT

printf '%s\n' \
  "PersonaLattice live-beta restore passed." \
  "Database: $PERSONALATTICE_DB_PATH" \
  "Restored from: $BACKUP_PATH" \
  "Backup SHA256: $EXPECTED_DIGEST" \
  "Restored SHA256: $RESTORED_DIGEST" \
  "Safety backup: ${SAFETY_BACKUP:-unavailable}" \
  "Restore evidence: $RESTORE_EVIDENCE" \
  "Release SHA: $RELEASE_SHA" \
  "Rollback SHA: $ROLLBACK_SHA" \
  "Integrity: ok"