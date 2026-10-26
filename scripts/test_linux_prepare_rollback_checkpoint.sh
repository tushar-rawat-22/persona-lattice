#!/usr/bin/env bash
# Disposable regression: failed prepare-release rollback must preserve unit evidence.
# Extracts the exact production function; never invokes real host preparation.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/deploy/linux/prepare-release.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
cat > "$TMP/bin/systemctl" <<'STUB'
#!/usr/bin/env bash
case "$1" in
  daemon-reload) [[ "$SCENARIO" != daemon-fail ]] ;;
  restart) [[ "$SCENARIO" != restart-fail ]] ;;
  *) exit 0 ;;
esac
STUB
chmod +x "$TMP/bin/systemctl"
python3 - "$SOURCE" "$TMP/harness.sh" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_text()
start = source.index("rollback_activation() {")
end = source.index("\n}\n", start) + 2
harness = (
    '#!/usr/bin/env bash\nset -euo pipefail\n'
    'CURRENT_LINK="$1/current"\nPREVIOUS_RELEASE="$1/prior"\n'
    'UNIT_TARGET="$1/installed-unit"\nUNIT_BACKUP="$1/unit-checkpoint"\n'
    'WAS_ENABLED=1\nWAS_ACTIVE=1\n'
    'wait_for_release_health() { [[ "$SCENARIO" == healthy ]]; }\n'
    + source[start:end] + '\n'
    'rc=0\nrollback_activation || rc=$?\n'
    'if [[ "$SCENARIO" == healthy ]]; then\n'
    '  [[ "$rc" -eq 0 && ! -e "$UNIT_BACKUP" ]] || { echo "FAIL healthy rollback did not clean checkpoint" >&2; exit 1; }\n'
    'else\n'
    '  [[ "$rc" -ne 0 && -f "$UNIT_BACKUP" ]] || { echo "FAIL $SCENARIO discarded checkpoint despite failed recovery (rc=$rc)" >&2; exit 1; }\n'
    'fi\n'
)
pathlib.Path(sys.argv[2]).write_text(harness)
PY
bash -n "$TMP/harness.sh"
for scenario in restart-fail daemon-fail healthy; do
  FIXTURE="$TMP/$scenario"
  mkdir -p "$FIXTURE/prior"
  printf 'original unit\n' > "$FIXTURE/unit-checkpoint"
  printf 'mutated unit\n' > "$FIXTURE/installed-unit"
  SCENARIO="$scenario" PATH="$TMP/bin:$PATH" bash "$TMP/harness.sh" "$FIXTURE"
  echo "PASS prepare-release rollback checkpoint $scenario"
done
