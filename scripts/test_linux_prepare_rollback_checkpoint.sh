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
printf '%s\n' "$1" >> "$MOCK_ACTION_LOG"
case "$1" in
  daemon-reload) [[ "$SCENARIO" != daemon-fail ]] ;;
  restart) [[ "$SCENARIO" != restart-fail ]] ;;
  enable|disable|stop) exit 0 ;;
  *) exit 99 ;;
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
    'WAS_ENABLED="$MOCK_WAS_ENABLED"\nWAS_ACTIVE="$MOCK_WAS_ACTIVE"\n'
    'wait_for_release_health() { [[ "$SCENARIO" != restart-fail && "$SCENARIO" != daemon-fail ]]; }\n'
    + source[start:end] + '\n'
    'rc=0\nrollback_activation || rc=$?\n'
    'if [[ "$SCENARIO" != restart-fail && "$SCENARIO" != daemon-fail ]]; then\n'
    '  [[ "$rc" -eq 0 && ! -e "$UNIT_BACKUP" ]] || { echo "FAIL healthy rollback did not clean checkpoint" >&2; exit 1; }\n'
    'else\n'
    '  [[ "$rc" -ne 0 && -f "$UNIT_BACKUP" ]] || { echo "FAIL $SCENARIO discarded checkpoint despite failed recovery (rc=$rc)" >&2; exit 1; }\n'
    'fi\n'
)
pathlib.Path(sys.argv[2]).write_text(harness)
PY
bash -n "$TMP/harness.sh"
for scenario in restart-fail daemon-fail healthy enabled-inactive disabled-active disabled-inactive; do
  FIXTURE="$TMP/$scenario"
  mkdir -p "$FIXTURE/prior"
  printf 'original unit\n' > "$FIXTURE/unit-checkpoint"
  printf 'mutated unit\n' > "$FIXTURE/installed-unit"
  : > "$FIXTURE/actions"
  enabled=1
  active=1
  case "$scenario" in
    enabled-inactive) active=0 ;;
    disabled-active) enabled=0 ;;
    disabled-inactive) enabled=0; active=0 ;;
  esac
  SCENARIO="$scenario" MOCK_WAS_ENABLED="$enabled" MOCK_WAS_ACTIVE="$active" \
    MOCK_ACTION_LOG="$FIXTURE/actions" PATH="$TMP/bin:$PATH" \
    bash "$TMP/harness.sh" "$FIXTURE"
  if [[ "$scenario" != restart-fail && "$scenario" != daemon-fail ]]; then
    expected_enable=disable
    [[ "$enabled" -eq 1 ]] && expected_enable=enable
    expected_activity=stop
    [[ "$active" -eq 1 ]] && expected_activity=restart
    grep -Fxq "$expected_enable" "$FIXTURE/actions" || {
      echo "FAIL $scenario did not restore prior enablement" >&2; exit 1;
    }
    grep -Fxq "$expected_activity" "$FIXTURE/actions" || {
      echo "FAIL $scenario did not restore prior activity" >&2; exit 1;
    }
    if [[ "$active" -eq 0 ]] && grep -Fxq restart "$FIXTURE/actions"; then
      echo "FAIL $scenario restarted previously inactive service" >&2; exit 1;
    fi
  fi
  echo "PASS prepare-release rollback checkpoint $scenario"
done
