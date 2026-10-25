#!/usr/bin/env bash
# Executable service-state regression for the prepared-release selector.
# All release paths and systemctl commands are disposable mocks; no real host state.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/deploy/linux/select-prepared-release.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/releases" "$TMP/systemd" "$TMP/runtime"
A="$(printf 'a%.0s' {1..40})"
B="$(printf 'b%.0s' {1..40})"
for sha in "$A" "$B"; do
  mkdir -p "$TMP/releases/$sha/deploy/linux"
  printf '%s\n' "$sha" > "$TMP/releases/$sha/deploy/linux/persona-lattice.service"
done
ln -s "$TMP/releases/$A" "$TMP/current"
cp "$TMP/releases/$A/deploy/linux/persona-lattice.service" "$TMP/systemd/persona-lattice.service"

# Only the test copy has rewritten paths and a disabled root precondition.
# Production code retains its root-only and ownership checks.
python3 - "$TMP" "$SOURCE" "$TMP/selector.sh" <<'PY'
import pathlib, sys
base, source, dest = sys.argv[1:]
s = pathlib.Path(source).read_text()
replacements = {
    'RELEASE_ROOT="/opt/persona-lattice/releases"': f'RELEASE_ROOT="{base}/releases"',
    'CURRENT_LINK="/opt/persona-lattice/current"': f'CURRENT_LINK="{base}/current"',
    'UNIT_TARGET="/etc/systemd/system/persona-lattice.service"': f'UNIT_TARGET="{base}/systemd/persona-lattice.service"',
    'RUNTIME_ROOT="/run/persona-lattice-release"': f'RUNTIME_ROOT="{base}/runtime"',
    'install -d -m 0700 -o root -g root "$RUNTIME_ROOT"': 'mkdir -p "$RUNTIME_ROOT"',
    '[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "run as root"': ': # root guard replaced ONLY in disposable test copy',
}
for old, new in replacements.items():
    if s.count(old) != 1:
        raise SystemExit(f"test source contract changed: {old}")
    s = s.replace(old, new)
pathlib.Path(dest).write_text(s)
PY
bash -n "$TMP/selector.sh"

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
  daemon-reload|enable|disable|stop)
    printf '%s\n' "$1" >> "$MOCK_MUTATION_LOG"
    exit 0 ;;
  restart)
    printf '%s\n' "$1" >> "$MOCK_MUTATION_LOG"
    exit "${MOCK_RESTART_EXIT:-0}" ;;
  *) exit 99 ;;
esac
STUB
cat > "$TMP/bin/stat" <<'STUB'
#!/usr/bin/env bash
[[ "$1" == '-c' && "$2" == '%u' ]] || exit 99
printf '0\n'
STUB
cat > "$TMP/bin/find" <<'STUB'
#!/usr/bin/env bash
# Root ownership/symlink traversal is covered by separate static contracts.
# This test isolates the service-state preflight only.
exit 0
STUB
cat > "$TMP/bin/curl" <<'STUB'
#!/usr/bin/env bash
# Simulate health loss only for the newly selected release, or for both releases.
case "${MOCK_HEALTH_FAIL_MODE:-none}" in
  all) exit 22 ;;
  selected)
    if [[ "$(readlink -f "$MOCK_CURRENT_LINK")" == "$MOCK_TARGET_RELEASE" ]]; then
      exit 22
    fi ;;
esac
exit 0
STUB
cat > "$TMP/bin/sleep" <<'STUB'
#!/usr/bin/env bash
# Keep forty health retries fast in disposable tests.
exit 0
STUB
cat > "$TMP/bin/install" <<'STUB'
#!/usr/bin/env bash
# Fail the first installed-unit replacement, but allow prior-state recovery.
if [[ "${MOCK_INSTALL_FAIL_ONCE:-0}" == 1
      && "${@: -1}" == "$MOCK_UNIT_TARGET"
      && ! -e "$MOCK_INSTALL_FAIL_MARKER" ]]; then
  : > "$MOCK_INSTALL_FAIL_MARKER"
  exit 55
fi
exec /usr/bin/install "$@"
STUB
chmod +x "$TMP/bin/"*
export PATH="$TMP/bin:$PATH"
export MOCK_MUTATION_LOG="$TMP/mutations"
export MOCK_CURRENT_LINK="$TMP/current"
export MOCK_TARGET_RELEASE="$TMP/releases/$B"
export MOCK_UNIT_TARGET="$TMP/systemd/persona-lattice.service"
export MOCK_INSTALL_FAIL_MARKER="$TMP/install-failed-once"

run_case() {
  local name="$1" allowed="$2" enabled_exit="$3" active_exit="$4"
  local unit_state="$5" active_state="$6" load_state="$7" show_exit="$8"
  export MOCK_ENABLED_EXIT="$enabled_exit" MOCK_ACTIVE_EXIT="$active_exit"
  export MOCK_UNIT_STATE="$unit_state" MOCK_ACTIVE_STATE="$active_state"
  export MOCK_LOAD_STATE="$load_state" MOCK_SHOW_EXIT="$show_exit"
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$TMP/runtime"/select-unit.*
  ln -s "$TMP/releases/$A" "$TMP/current"
  cp "$TMP/releases/$A/deploy/linux/persona-lattice.service" "$TMP/systemd/persona-lattice.service"
  local rc=0
  bash "$TMP/selector.sh" "$B" > "$TMP/stdout" 2> "$TMP/stderr" || rc=$?
  if [[ "$allowed" == yes ]]; then
    [[ "$rc" == 0 && "$(readlink -f "$TMP/current")" == "$TMP/releases/$B" ]] || {
      echo "FAIL $name expected prepared selection (rc=$rc)" >&2
      cat "$TMP/stderr" >&2
      exit 1
    }
  else
    [[ "$rc" != 0 && "$(readlink -f "$TMP/current")" == "$TMP/releases/$A" ]] || {
      echo "FAIL $name changed current selection (rc=$rc)" >&2
      exit 1
    }
    [[ "$(cat "$TMP/systemd/persona-lattice.service")" == "$A" && ! -e "$MOCK_MUTATION_LOG" ]] || {
      echo "FAIL $name changed unit or called mutating systemctl" >&2
      exit 1
    }
    if compgen -G "$TMP/runtime/select-unit.*" >/dev/null; then
      echo "FAIL $name created a rollback checkpoint before trusted state" >&2
      exit 1
    fi
  fi
  echo "PASS $name"
}

run_case enabled-active yes 0 0 enabled active loaded 0
run_case disabled-inactive yes 1 3 disabled inactive loaded 0
run_case enabled-command-error no 127 0 enabled active loaded 0
run_case enabled-unknown-exit no 2 0 enabled active loaded 0
run_case active-command-error no 0 127 enabled inactive loaded 0
for code in 1 2 4 5; do
  run_case "active-unexpected-$code" no 0 "$code" enabled inactive loaded 0
done
run_case active-state-contradiction no 0 0 enabled inactive loaded 0
run_case enabled-state-contradiction no 0 0 disabled active loaded 0
run_case inactive-state-contradiction no 1 3 disabled active active 0
run_case masked-unit no 1 3 masked inactive loaded 0
run_case missing-unit no 1 3 disabled inactive not-found 0
run_case show-query-error no 0 0 enabled active loaded 127

# Force the selected release and the attempted prior-release recovery to fail
# restarting. The operator must retain the root-only unit checkpoint for manual
# recovery when the prior state cannot be fully restored.
run_failed_restart_checkpoint_case() {
  export MOCK_ENABLED_EXIT=0 MOCK_ACTIVE_EXIT=0
  export MOCK_UNIT_STATE=enabled MOCK_ACTIVE_STATE=active MOCK_LOAD_STATE=loaded
  export MOCK_SHOW_EXIT=0 MOCK_RESTART_EXIT=1
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$TMP/runtime"/select-unit.*
  ln -s "$TMP/releases/$A" "$TMP/current"
  cp "$TMP/releases/$A/deploy/linux/persona-lattice.service" "$TMP/systemd/persona-lattice.service"
  local rc=0
  bash "$TMP/selector.sh" "$B" > "$TMP/stdout" 2> "$TMP/stderr" || rc=$?
  [[ "$rc" != 0 ]] || { echo "FAIL restart-recovery-failure unexpectedly succeeded" >&2; exit 1; }
  [[ "$(readlink -f "$TMP/current")" == "$TMP/releases/$A" ]] || {
    echo "FAIL restart-recovery-failure did not restore prior release link" >&2; exit 1;
  }
  [[ "$(cat "$TMP/systemd/persona-lattice.service")" == "$A" ]] || {
    echo "FAIL restart-recovery-failure did not restore prior unit" >&2; exit 1;
  }
  if ! compgen -G "$TMP/runtime/select-unit.*" >/dev/null; then
    echo "FAIL restart-recovery-failure discarded unit checkpoint despite failed recovery" >&2
    exit 1
  fi
  [[ "$(grep -c restart "$MOCK_MUTATION_LOG")" == 2 ]] || {
    echo "FAIL restart-recovery-failure did not exercise both restart attempts" >&2; exit 1;
  }
  unset MOCK_RESTART_EXIT
  echo "PASS restart-recovery-failure preserves unit checkpoint"
}
run_failed_restart_checkpoint_case

# Health failure must restore the old release, its installed unit and service
# authority. If the prior release also fails health, retain the unit checkpoint.
run_health_failure_case() {
  local mode="$1" rc=0
  export MOCK_ENABLED_EXIT=0 MOCK_ACTIVE_EXIT=0
  export MOCK_UNIT_STATE=enabled MOCK_ACTIVE_STATE=active MOCK_LOAD_STATE=loaded
  export MOCK_SHOW_EXIT=0 MOCK_HEALTH_FAIL_MODE="$mode"
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$TMP/runtime"/select-unit.*
  ln -s "$TMP/releases/$A" "$TMP/current"
  cp "$TMP/releases/$A/deploy/linux/persona-lattice.service" "$TMP/systemd/persona-lattice.service"
  bash "$TMP/selector.sh" "$B" > "$TMP/stdout" 2> "$TMP/stderr" || rc=$?
  [[ "$rc" != 0 ]] || { echo "FAIL health-$mode unexpectedly succeeded" >&2; exit 1; }
  [[ "$(readlink -f "$TMP/current")" == "$TMP/releases/$A" ]] || {
    echo "FAIL health-$mode did not restore previous release" >&2; exit 1;
  }
  [[ "$(cat "$TMP/systemd/persona-lattice.service")" == "$A" ]] || {
    echo "FAIL health-$mode did not restore previous unit" >&2; exit 1;
  }
  [[ "$(grep -c restart "$MOCK_MUTATION_LOG")" == 2 ]] || {
    echo "FAIL health-$mode did not exercise both restarts" >&2; exit 1;
  }
  if [[ "$mode" == selected ]]; then
    if compgen -G "$TMP/runtime/select-unit.*" >/dev/null; then
      echo "FAIL health-selected left a checkpoint after verified recovery" >&2; exit 1;
    fi
  else
    if ! compgen -G "$TMP/runtime/select-unit.*" >/dev/null; then
      echo "FAIL health-all discarded checkpoint after unverified recovery" >&2; exit 1;
    fi
  fi
  unset MOCK_HEALTH_FAIL_MODE
  echo "PASS health-$mode restores prior selection; checkpoint retention matches recovery"
}
run_health_failure_case selected
run_health_failure_case all

# Simulate a partial forward mutation: the symlink changes, then installing the
# selected systemd unit fails. Recovery must restore both paths and remove the
# checkpoint only after the previous service passes health.
run_unit_install_failure_case() {
  local rc=0
  export MOCK_ENABLED_EXIT=0 MOCK_ACTIVE_EXIT=0
  export MOCK_UNIT_STATE=enabled MOCK_ACTIVE_STATE=active MOCK_LOAD_STATE=loaded
  export MOCK_SHOW_EXIT=0 MOCK_INSTALL_FAIL_ONCE=1
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$MOCK_INSTALL_FAIL_MARKER" "$TMP/runtime"/select-unit.*
  ln -s "$TMP/releases/$A" "$TMP/current"
  cp "$TMP/releases/$A/deploy/linux/persona-lattice.service" "$TMP/systemd/persona-lattice.service"
  bash "$TMP/selector.sh" "$B" > "$TMP/stdout" 2> "$TMP/stderr" || rc=$?
  [[ "$rc" != 0 && -e "$MOCK_INSTALL_FAIL_MARKER" ]] || {
    echo "FAIL unit-install-failure did not exercise failed forward installation" >&2; exit 1;
  }
  [[ "$(readlink -f "$TMP/current")" == "$TMP/releases/$A" ]] || {
    echo "FAIL unit-install-failure did not restore previous release" >&2; exit 1;
  }
  [[ "$(cat "$TMP/systemd/persona-lattice.service")" == "$A" ]] || {
    echo "FAIL unit-install-failure did not restore previous unit" >&2; exit 1;
  }
  if compgen -G "$TMP/runtime/select-unit.*" >/dev/null; then
    echo "FAIL unit-install-failure left checkpoint after verified recovery" >&2; exit 1;
  fi
  unset MOCK_INSTALL_FAIL_ONCE
  echo "PASS unit-install-failure restores prior release/unit after partial mutation"
}
run_unit_install_failure_case

echo "PASS prepared-release selector service-state and failure-atomic recovery mocks."
