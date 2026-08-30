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
conn.execute("insert into evidence(summary) values (?)", ("synthetic retained evidence",))
conn.commit(); conn.close()
PY
printf 'PERSONALATTICE_DB_PATH=%q\n' "$DB" >"$ENV_FILE"
chmod 600 "$ENV_FILE"
mkdir -p "$RUNTIME"
chmod 700 "$RUNTIME"
printf 'release_sha=%s\nrollback_sha=%s\n' "$RELEASE_SHA" "$ROLLBACK_SHA" >"$RELEASE_MANIFEST"
chmod 600 "$RELEASE_MANIFEST"

OUTPUT="$(PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" PERSONALATTICE_LIVE_RUNTIME_DIR="$RUNTIME" bash "$ROOT/scripts/live_beta_backup.sh")"
printf '%s\n' "$OUTPUT"
BACKUP="$(printf '%s\n' "$OUTPUT" | sed -n 's/^Backup: //p')"
EVIDENCE="$(printf '%s\n' "$OUTPUT" | sed -n 's/^Evidence: //p')"
DIGEST="$(printf '%s\n' "$OUTPUT" | sed -n 's/^SHA256: //p')"
[[ -n "$BACKUP" && -f "$BACKUP" ]]
[[ -n "$EVIDENCE" && -f "$EVIDENCE" ]]
[[ "$(stat -c '%a' "$BACKUP" 2>/dev/null || stat -f '%Lp' "$BACKUP")" == "600" ]]
[[ "$(stat -c '%a' "$EVIDENCE" 2>/dev/null || stat -f '%Lp' "$EVIDENCE")" == "600" ]]
printf '%s\n' "$OUTPUT" | grep -q "^Release SHA: $RELEASE_SHA$"
printf '%s\n' "$OUTPUT" | grep -q "^Rollback SHA: $ROLLBACK_SHA$"
printf '%s\n' "$OUTPUT" | grep -q '^Integrity: ok$'
printf '%s\n' "$OUTPUT" | grep -q '^Restore check: ok$'
grep -q "^backup_sha256=$DIGEST$" "$EVIDENCE"
grep -q "^release_sha=$RELEASE_SHA$" "$EVIDENCE"
grep -q "^rollback_sha=$ROLLBACK_SHA$" "$EVIDENCE"

python3 - "$BACKUP" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
assert conn.execute("pragma integrity_check").fetchone()[0] == "ok"
assert conn.execute("select summary from evidence").fetchone()[0] == "synthetic retained evidence"
conn.close()
PY

chmod 644 "$ENV_FILE"
if PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" PERSONALATTICE_LIVE_RUNTIME_DIR="$RUNTIME" bash "$ROOT/scripts/live_beta_backup.sh" >"$TMP/out" 2>"$TMP/err"; then
  echo "backup unexpectedly accepted a non-owner-only environment file" >&2
  exit 1
fi
grep -q 'production environment file must be owner-only' "$TMP/err"

chmod 600 "$ENV_FILE"
printf 'release_sha=not-a-commit\nrollback_sha=%s\n' "$ROLLBACK_SHA" >"$RELEASE_MANIFEST"
chmod 600 "$RELEASE_MANIFEST"
if PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE" PERSONALATTICE_BACKUP_DIR="$BACKUPS" PERSONALATTICE_LIVE_RUNTIME_DIR="$RUNTIME" bash "$ROOT/scripts/live_beta_backup.sh" >"$TMP/out" 2>"$TMP/err"; then
  echo "backup unexpectedly accepted malformed release provenance" >&2
  exit 1
fi
grep -q 'release manifest could not be parsed safely' "$TMP/err"
