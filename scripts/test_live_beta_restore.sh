#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
DB="$TMP/cases.db"
ENV_FILE="$TMP/production.env"
BACKUPS="$TMP/backups"
RUNTIME="$TMP/live"
RELEASE_MANIFEST="$RUNTIME/release.env"
RELEASE_SHA="1111111111111111111111111111111111111111"
ROLLBACK_SHA="2222222222222222222222222222222222222222"

python3 - "$DB" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("create table evidence (id integer primary key, summary text not null)")
conn.execute("insert into evidence(summary) values (?)", ("original retained evidence",))
conn.commit(); conn.close()
PY
printf 'PERSONALATTICE_DB_PATH=%q\n' "$DB" >"$ENV_FILE"
chmod 600 "$ENV_FILE"
mkdir -p "$RUNTIME"
chmod 700 "$RUNTIME"
printf 'release_sha=%s\nrollback_sha=%s\n' "$RELEASE_SHA" "$ROLLBACK_SHA" >"$RELEASE_MANIFEST"
chmod 600 "$RELEASE_MANIFEST"

BACKUP_OUTPUT="$(PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" PERSONALATTICE_LIVE_RUNTIME_DIR="$RUNTIME" bash "$ROOT/scripts/live_beta_backup.sh")"
BACKUP="$(printf '%s\n' "$BACKUP_OUTPUT" | sed -n 's/^Backup: //p')"
[[ -n "$BACKUP" && -f "$BACKUP" ]]

python3 - "$DB" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("update evidence set summary = ? where id = 1", ("mutated after backup",))
conn.commit(); conn.close()
PY

RESTORE_OUTPUT="$(PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" bash "$ROOT/scripts/live_beta_restore.sh" "$BACKUP" --confirm-offline)"
printf '%s\n' "$RESTORE_OUTPUT"
printf '%s\n' "$RESTORE_OUTPUT" | grep -q '^PersonaLattice live-beta restore passed\.$'
printf '%s\n' "$RESTORE_OUTPUT" | grep -q '^Integrity: ok$'
printf '%s\n' "$RESTORE_OUTPUT" | grep -q "^Release SHA: $RELEASE_SHA$"
printf '%s\n' "$RESTORE_OUTPUT" | grep -q "^Rollback SHA: $ROLLBACK_SHA$"
SAFETY_BACKUP="$(printf '%s\n' "$RESTORE_OUTPUT" | sed -n 's/^Safety backup: //p')"
RESTORE_EVIDENCE="$(printf '%s\n' "$RESTORE_OUTPUT" | sed -n 's/^Restore evidence: //p')"
[[ -f "$SAFETY_BACKUP" ]]
[[ -f "$RESTORE_EVIDENCE" ]]
[[ "$(stat -c '%a' "$DB" 2>/dev/null || stat -f '%Lp' "$DB")" == "600" ]]
[[ "$(stat -c '%a' "$SAFETY_BACKUP" 2>/dev/null || stat -f '%Lp' "$SAFETY_BACKUP")" == "600" ]]
[[ "$(stat -c '%a' "$RESTORE_EVIDENCE" 2>/dev/null || stat -f '%Lp' "$RESTORE_EVIDENCE")" == "600" ]]

python3 - "$DB" "$SAFETY_BACKUP" <<'PY'
import sqlite3, sys
restored = sqlite3.connect(sys.argv[1])
assert restored.execute("pragma integrity_check").fetchone()[0] == "ok"
assert restored.execute("select summary from evidence").fetchone()[0] == "original retained evidence"
restored.close()
safety = sqlite3.connect(sys.argv[2])
assert safety.execute("pragma integrity_check").fetchone()[0] == "ok"
assert safety.execute("select summary from evidence").fetchone()[0] == "mutated after backup"
safety.close()
PY

grep -q "^restored_from=$BACKUP$" "$RESTORE_EVIDENCE"
grep -q "^release_sha=$RELEASE_SHA$" "$RESTORE_EVIDENCE"
grep -q "^rollback_sha=$ROLLBACK_SHA$" "$RESTORE_EVIDENCE"
grep -q "^safety_backup=$SAFETY_BACKUP$" "$RESTORE_EVIDENCE"

if PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" bash "$ROOT/scripts/live_beta_restore.sh" "$BACKUP" >"$TMP/out" 2>"$TMP/err"; then
  echo "restore unexpectedly ran without explicit offline confirmation" >&2
  exit 1
fi
grep -q 'usage: scripts/live_beta_restore.sh BACKUP.sqlite3 --confirm-offline' "$TMP/err"

cp "$BACKUP" "$TMP/tampered.sqlite3"
cp "$BACKUP.env" "$TMP/tampered.sqlite3.env"
printf 'tamper' >>"$TMP/tampered.sqlite3"
chmod 600 "$TMP/tampered.sqlite3" "$TMP/tampered.sqlite3.env"
if PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" bash "$ROOT/scripts/live_beta_restore.sh" "$TMP/tampered.sqlite3" --confirm-offline >"$TMP/out" 2>"$TMP/err"; then
  echo "restore unexpectedly accepted a backup whose digest does not match evidence" >&2
  exit 1
fi
grep -q 'backup digest does not match evidence' "$TMP/err"

chmod 644 "$BACKUP.env"
if PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" bash "$ROOT/scripts/live_beta_restore.sh" "$BACKUP" --confirm-offline >"$TMP/out" 2>"$TMP/err"; then
  echo "restore unexpectedly accepted non-owner-only backup evidence" >&2
  exit 1
fi
grep -q 'backup evidence file must be owner-only' "$TMP/err"