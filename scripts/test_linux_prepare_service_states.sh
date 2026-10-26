#!/usr/bin/env bash
# Disposable regression for prepare-release's pre-activation systemd authority.
# Extracts the exact production block; never executes release preparation.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/deploy/linux/prepare-release.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
cat > "$TMP/bin/systemctl" <<'STUB'
#!/usr/bin/env bash
case "$1" in
  is-enabled) exit "$MOCK_ENABLED_EXIT" ;;
  is-active) exit "$MOCK_ACTIVE_EXIT" ;;
  show)
    [[ "$MOCK_SHOW_EXIT" == 0 ]] || exit "$MOCK_SHOW_EXIT"
    case "$2" in
      --property=LoadState) printf '%s\n' "$MOCK_LOAD_STATE" ;;
      --property=ActiveState) printf '%s\n' "$MOCK_ACTIVE_STATE" ;;
      --property=UnitFileState) printf '%s\n' "$MOCK_UNIT_STATE" ;;
      *) exit 99 ;;
    esac ;;
  *) echo "Unexpected systemctl mutation: $*" >&2; exit 99 ;;
esac
STUB
chmod +x "$TMP/bin/systemctl"
python3 - "$SOURCE" "$TMP/harness.sh" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_text()
start = source.index("WAS_ENABLED=0\n")
end = source.index("\n# Only checkpoint the installed unit after prior systemd state is unambiguous.", start)
block = source[start:end]
harness = (
    '#!/usr/bin/env bash\nset -euo pipefail\n'
    'PREVIOUS_RELEASE="${MOCK_PREVIOUS_RELEASE:-}"\n'
    'UNIT_TARGET="$MOCK_UNIT_TARGET"\n'
    'fail() { printf "DENY %s\\n" "$1" >&2; exit 1; }\n'
    + block + '\n'
    'printf "%s:%s\\n" "$WAS_ENABLED" "${WAS_ACTIVE:-unknown}" > "$MOCK_SENTINEL"\n'
)
pathlib.Path(sys.argv[2]).write_text(harness)
PY
bash -n "$TMP/harness.sh"
export PATH="$TMP/bin:$PATH"
export MOCK_UNIT_TARGET="$TMP/installed-unit" MOCK_SENTINEL="$TMP/activation-sentinel"
run_case() {
  local name="$1" allowed="$2" enabled_exit="$3" active_exit="$4"
  local load_state="$5" active_state="$6" unit_state="$7" show_exit="$8"
  local prior="$9" expected="${10:-}"
  export MOCK_ENABLED_EXIT="$enabled_exit" MOCK_ACTIVE_EXIT="$active_exit"
  export MOCK_LOAD_STATE="$load_state" MOCK_ACTIVE_STATE="$active_state"
  export MOCK_UNIT_STATE="$unit_state" MOCK_SHOW_EXIT="$show_exit"
  export MOCK_PREVIOUS_RELEASE="$prior"
  rm -f "$MOCK_SENTINEL" "$MOCK_UNIT_TARGET"
  if [[ -n "$prior" ]]; then
    printf 'installed unit\n' > "$MOCK_UNIT_TARGET"
  fi
  local rc=0
  bash "$TMP/harness.sh" > "$TMP/stdout" 2> "$TMP/stderr" || rc=$?
  if [[ "$allowed" == yes ]]; then
    [[ "$rc" == 0 && -f "$MOCK_SENTINEL" && "$(cat "$MOCK_SENTINEL")" == "$expected" ]] || {
      echo "FAIL $name denied valid state or lost prior authority (rc=$rc)" >&2
      cat "$TMP/stderr" >&2
      exit 1
    }
  else
    [[ "$rc" != 0 && ! -e "$MOCK_SENTINEL" ]] || {
      echo "FAIL $name authorized ambiguous state (rc=$rc)" >&2
      exit 1
    }
  fi
  echo "PASS prepare-release preflight $name"
}
run_case enabled-active yes 0 0 loaded active enabled 0 prior 1:1
run_case enabled-inactive yes 0 3 loaded inactive enabled 0 prior 1:0
run_case disabled-inactive yes 1 3 loaded inactive disabled 0 prior 0:0
run_case disabled-active yes 1 0 loaded active disabled 0 prior 0:1
for rc in 2 4 5 127; do
  run_case "enabled-error-$rc" no "$rc" 3 loaded inactive disabled 0 prior
  run_case "active-error-$rc" no 1 "$rc" loaded inactive disabled 0 prior
done
run_case enabled-contradiction no 0 3 loaded inactive disabled 0 prior
run_case active-contradiction no 1 0 loaded inactive disabled 0 prior
run_case missing-load no 1 3 not-found inactive disabled 0 prior
run_case masked-unit no 1 3 loaded inactive masked 0 prior
run_case show-command-error no 1 3 loaded inactive disabled 1 prior
run_case first-install yes 4 3 not-found inactive "" 0 "" 0:0
run_case first-install-stale-loaded no 4 3 loaded inactive "" 0 ""
run_case first-install-stale-unit no 4 3 not-found inactive enabled 0 ""
