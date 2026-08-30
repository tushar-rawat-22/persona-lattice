#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
DB="$TMP/cases.db"
ENV_FILE="$TMP/production.env"
BACKUPS="$TMP/backups"

python3 - "$DB" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("create table evidence (id integer primary key, summary text not null)")
conn.execute("insert into evidence(summary) values (?)", ("synthetic retained evidence",))
conn.commit(); conn.close()
PY
printf 'PERSONALATTICE_DB_PATH=%q\n' "$DB" >"$ENV_FILE"
chmod 600 "$ENV_FILE"

OUTPUT="$(PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" bash "$ROOT/scripts/live_beta_backup.sh")"
printf '%s\n' "$OUTPUT"
BACKUP="$(printf '%s\n' "$OUTPUT" | sed -n 's/^Backup: //p')"
[[ -n "$BACKUP" && -f "$BACKUP" ]]
[[ "$(stat -c '%a' "$BACKUP" 2>/dev/null || stat -f '%Lp' "$BACKUP")" == "600" ]]
printf '%s\n' "$OUTPUT" | grep -q '^Integrity: ok$'
printf '%s\n' "$OUTPUT" | grep -q '^Restore check: ok$'

python3 - "$BACKUP" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
assert conn.execute("pragma integrity_check").fetchone()[0] == "ok"
assert conn.execute("select summary from evidence").fetchone()[0] == "synthetic retained evidence"
conn.close()
PY

chmod 644 "$ENV_FILE"
if PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" bash "$ROOT/scripts/live_beta_backup.sh" >"$TMP/out" 2>"$TMP/err"; then
  echo "backup unexpectedly accepted a non-owner-only environment file" >&2
  exit 1
fi
grep -q 'production environment file must be owner-only' "$TMP/err"
