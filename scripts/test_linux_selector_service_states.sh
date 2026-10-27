#!/usr/bin/env bash
# Executable service-state regression for the prepared-release selector.
# All release paths and systemctl commands are disposable mocks; no real host state.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/deploy/linux/select-prepared-release.sh"
TMP="$(mktemp -d)"
TMP="$(cd "$TMP" && pwd -P)"
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
# Model a retained path that violates the root-owned/non-writable invariant.
if [[ -n "${MOCK_UNSAFE_PATH:-}" && " $* " == *" -print -quit "* ]]; then
  printf '%s\n' "$MOCK_UNSAFE_PATH"
  exit 0
fi
# A failed symlink enumeration must abort before any release mutation.
# This models a filesystem/find error on the second retained-tree scan.
if [[ "${MOCK_FIND_SYMLINK_SCAN_EXIT:-0}" != 0 && " $* " == *" -print0 "* ]]; then
  exit "$MOCK_FIND_SYMLINK_SCAN_EXIT"
fi
if [[ -n "${MOCK_SYMLINK_PATH:-}" && " $* " == *" -print0 "* ]]; then
  printf '%s\0' "$MOCK_SYMLINK_PATH"
fi
# Other root ownership and symlink traversal checks have separate contracts.
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
cat > "$TMP/bin/ln" <<'STUB'
#!/usr/bin/env bash
# The previous release identity and service authority must be durably recorded
# before /current is switched. Inspect the forward switch before delegating.
if [[ "${MOCK_REQUIRE_SELECTION_CHECKPOINT:-0}" == 1
      && "${@: -2:1}" == "$MOCK_TARGET_RELEASE"
      && "${@: -1}" == "$MOCK_CURRENT_LINK" ]]; then
  checkpoint="$(compgen -G "$MOCK_RUNTIME_ROOT/select-state.*" | head -n 1 || true)"
  [[ -f "$checkpoint" ]] || exit 56
  grep -Fxq "previous_release=$MOCK_PREVIOUS_RELEASE" "$checkpoint" || exit 57
  grep -Fxq "previous_sha=$MOCK_PREVIOUS_SHA" "$checkpoint" || exit 58
  grep -Fxq "service_enabled=$MOCK_EXPECTED_ENABLED" "$checkpoint" || exit 59
  grep -Fxq "service_active=$MOCK_EXPECTED_ACTIVE" "$checkpoint" || exit 60
  unit_checkpoint="$(sed -n 's/^unit_checkpoint=//p' "$checkpoint")"
  [[ -f "$unit_checkpoint" ]] || exit 61
fi
exec /bin/ln "$@"
STUB
chmod +x "$TMP/bin/"*
export PATH="$TMP/bin:$PATH"
export MOCK_MUTATION_LOG="$TMP/mutations"
export MOCK_CURRENT_LINK="$TMP/current"
export MOCK_TARGET_RELEASE="$TMP/releases/$B"
export MOCK_UNIT_TARGET="$TMP/systemd/persona-lattice.service"
export MOCK_INSTALL_FAIL_MARKER="$TMP/install-failed-once"
export MOCK_RUNTIME_ROOT="$TMP/runtime"
export MOCK_PREVIOUS_RELEASE="$TMP/releases/$A"
export MOCK_PREVIOUS_SHA="$A"

run_case() {
  local name="$1" allowed="$2" enabled_exit="$3" active_exit="$4"
  local unit_state="$5" active_state="$6" load_state="$7" show_exit="$8"
  export MOCK_ENABLED_EXIT="$enabled_exit" MOCK_ACTIVE_EXIT="$active_exit"
  export MOCK_UNIT_STATE="$unit_state" MOCK_ACTIVE_STATE="$active_state"
  export MOCK_LOAD_STATE="$load_state" MOCK_SHOW_EXIT="$show_exit"
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$TMP/runtime"/select-unit.* "$TMP/runtime"/select-state.*
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
    local expected_enablement expected_activity
    [[ "$unit_state" == enabled ]] && expected_enablement=enable || expected_enablement=disable
    [[ "$active_state" == active ]] && expected_activity=restart || expected_activity=stop
    grep -Fxq "$expected_enablement" "$MOCK_MUTATION_LOG" \
      || { echo "FAIL $name lost enablement authority" >&2; exit 1; }
    grep -Fxq "$expected_activity" "$MOCK_MUTATION_LOG" \
      || { echo "FAIL $name lost activity authority" >&2; exit 1; }
  else
    [[ "$rc" != 0 && "$(readlink -f "$TMP/current")" == "$TMP/releases/$A" ]] || {
      echo "FAIL $name changed current selection (rc=$rc)" >&2
      exit 1
    }
    [[ "$(cat "$TMP/systemd/persona-lattice.service")" == "$A" && ! -e "$MOCK_MUTATION_LOG" ]] || {
      echo "FAIL $name changed unit or called mutating systemctl" >&2
      exit 1
    }
    if compgen -G "$TMP/runtime/select-unit.*" >/dev/null \
      || compgen -G "$TMP/runtime/select-state.*" >/dev/null; then
      echo "FAIL $name created a rollback checkpoint before trusted state" >&2
      exit 1
    fi
  fi
  echo "PASS $name"
}

run_case enabled-active yes 0 0 enabled active loaded 0
run_case disabled-inactive yes 1 3 disabled inactive loaded 0
run_case enabled-inactive yes 0 3 enabled inactive loaded 0
run_case disabled-active yes 1 0 disabled active loaded 0
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

# The original process-substitution loop discarded find's nonzero exit status.
# No release, unit, systemd mutation or rollback checkpoint may be created.
export MOCK_FIND_SYMLINK_SCAN_EXIT=74
run_case retained-symlink-scan-error no 0 0 enabled active loaded 0
unset MOCK_FIND_SYMLINK_SCAN_EXIT

assert_preflight_rejects() {
  local name="$1" target="$2" rc=0
  export MOCK_ENABLED_EXIT=0 MOCK_ACTIVE_EXIT=0
  export MOCK_UNIT_STATE=enabled MOCK_ACTIVE_STATE=active MOCK_LOAD_STATE=loaded MOCK_SHOW_EXIT=0
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$TMP/runtime"/select-unit.* "$TMP/runtime"/select-state.*
  ln -s "$TMP/releases/$A" "$TMP/current"
  cp "$TMP/releases/$A/deploy/linux/persona-lattice.service" "$TMP/systemd/persona-lattice.service"
  bash "$TMP/selector.sh" "$target" > "$TMP/stdout" 2> "$TMP/stderr" || rc=$?
  [[ "$rc" != 0 && "$(readlink -f "$TMP/current")" == "$TMP/releases/$A" ]] || {
    echo "FAIL $name did not fail closed before release selection" >&2; exit 1;
  }
  [[ "$(cat "$TMP/systemd/persona-lattice.service")" == "$A" && ! -e "$MOCK_MUTATION_LOG" ]] || {
    echo "FAIL $name changed installed unit or service state" >&2; exit 1;
  }
  if compgen -G "$TMP/runtime/select-unit.*" >/dev/null \
    || compgen -G "$TMP/runtime/select-state.*" >/dev/null; then
    echo "FAIL $name allocated recovery evidence before trusted preflight" >&2
    exit 1
  fi
  echo "PASS $name"
}

assert_preflight_rejects invalid-sha not-a-full-lowercase-sha
C="$(printf 'c%.0s' {1..40})"
assert_preflight_rejects missing-release "$C"
ln -s "$TMP/releases/$B" "$TMP/releases/$C"
assert_preflight_rejects symlink-release "$C"
rm -f "$TMP/releases/$C"

touch "$TMP/releases/$B/unsafe-state"
export MOCK_UNSAFE_PATH="$TMP/releases/$B/unsafe-state"
assert_preflight_rejects unsafe-retained-permissions "$B"
unset MOCK_UNSAFE_PATH

ln -s "$TMP/releases/$B/missing" "$TMP/releases/$B/broken-link"
export MOCK_SYMLINK_PATH="$TMP/releases/$B/broken-link"
assert_preflight_rejects broken-retained-symlink "$B"
rm -f "$TMP/releases/$B/broken-link"

mkdir -p "$TMP/outside"
ln -s "$TMP/outside" "$TMP/releases/$B/escaping-link"
export MOCK_SYMLINK_PATH="$TMP/releases/$B/escaping-link"
assert_preflight_rejects escaping-retained-symlink "$B"
unset MOCK_SYMLINK_PATH
rm -f "$TMP/releases/$B/escaping-link"

# The selector must persist the prior release identity, unit checkpoint and
# enabled/active authority before the first /current mutation, then remove both
# checkpoints after a verified successful selection.
run_selection_checkpoint_case() {
  local rc=0
  export MOCK_ENABLED_EXIT=0 MOCK_ACTIVE_EXIT=0
  export MOCK_UNIT_STATE=enabled MOCK_ACTIVE_STATE=active MOCK_LOAD_STATE=loaded
  export MOCK_SHOW_EXIT=0 MOCK_REQUIRE_SELECTION_CHECKPOINT=1
  export MOCK_EXPECTED_ENABLED=1 MOCK_EXPECTED_ACTIVE=1
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$TMP/runtime"/select-unit.* "$TMP/runtime"/select-state.*
  ln -s "$TMP/releases/$A" "$TMP/current"
  cp "$TMP/releases/$A/deploy/linux/persona-lattice.service" "$TMP/systemd/persona-lattice.service"
  bash "$TMP/selector.sh" "$B" > "$TMP/stdout" 2> "$TMP/stderr" || rc=$?
  [[ "$rc" == 0 && "$(readlink -f "$TMP/current")" == "$TMP/releases/$B" ]] || {
    echo "FAIL selection-checkpoint was absent before switch or selection failed (rc=$rc)" >&2
    cat "$TMP/stderr" >&2
    exit 1
  }
  if compgen -G "$TMP/runtime/select-unit.*" >/dev/null \
    || compgen -G "$TMP/runtime/select-state.*" >/dev/null; then
    echo "FAIL selection-checkpoint was not cleaned after verified success" >&2
    exit 1
  fi
  unset MOCK_REQUIRE_SELECTION_CHECKPOINT MOCK_EXPECTED_ENABLED MOCK_EXPECTED_ACTIVE
  echo "PASS selection-checkpoint precedes switch and cleans after success"
}
run_selection_checkpoint_case

# Force the selected release and the attempted prior-release recovery to fail
# restarting. The operator must retain the root-only unit checkpoint for manual
# recovery when the prior state cannot be fully restored.
run_failed_restart_checkpoint_case() {
  export MOCK_ENABLED_EXIT=0 MOCK_ACTIVE_EXIT=0
  export MOCK_UNIT_STATE=enabled MOCK_ACTIVE_STATE=active MOCK_LOAD_STATE=loaded
  export MOCK_SHOW_EXIT=0 MOCK_RESTART_EXIT=1
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$TMP/runtime"/select-unit.* "$TMP/runtime"/select-state.*
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
  selection_checkpoint="$(compgen -G "$TMP/runtime/select-state.*" | head -n 1 || true)"
  [[ -f "$selection_checkpoint" ]] || {
    echo "FAIL restart-recovery-failure discarded prior selection identity" >&2; exit 1;
  }
  grep -Fxq "previous_release=$TMP/releases/$A" "$selection_checkpoint" || {
    echo "FAIL restart-recovery-failure retained the wrong prior selection" >&2; exit 1;
  }
  [[ "$(grep -c restart "$MOCK_MUTATION_LOG")" == 2 ]] || {
    echo "FAIL restart-recovery-failure did not exercise both restart attempts" >&2; exit 1;
  }
  unset MOCK_RESTART_EXIT
  echo "PASS restart-recovery-failure preserves recovery checkpoints"
}
run_failed_restart_checkpoint_case

# Health failure must restore the old release, its installed unit and service
# authority. If the prior release also fails health, retain the unit checkpoint.
run_health_failure_case() {
  local mode="$1" rc=0
  export MOCK_ENABLED_EXIT=0 MOCK_ACTIVE_EXIT=0
  export MOCK_UNIT_STATE=enabled MOCK_ACTIVE_STATE=active MOCK_LOAD_STATE=loaded
  export MOCK_SHOW_EXIT=0 MOCK_HEALTH_FAIL_MODE="$mode"
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$TMP/runtime"/select-unit.* "$TMP/runtime"/select-state.*
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
    if compgen -G "$TMP/runtime/select-unit.*" >/dev/null \
      || compgen -G "$TMP/runtime/select-state.*" >/dev/null; then
      echo "FAIL health-selected left a checkpoint after verified recovery" >&2; exit 1;
    fi
  else
    if ! compgen -G "$TMP/runtime/select-unit.*" >/dev/null \
      || ! compgen -G "$TMP/runtime/select-state.*" >/dev/null; then
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
  rm -f "$TMP/current" "$MOCK_MUTATION_LOG" "$MOCK_INSTALL_FAIL_MARKER" "$TMP/runtime"/select-unit.* "$TMP/runtime"/select-state.*
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
  if compgen -G "$TMP/runtime/select-unit.*" >/dev/null \
    || compgen -G "$TMP/runtime/select-state.*" >/dev/null; then
    echo "FAIL unit-install-failure left checkpoint after verified recovery" >&2; exit 1;
  fi
  unset MOCK_INSTALL_FAIL_ONCE
  echo "PASS unit-install-failure restores prior release/unit after partial mutation"
}
run_unit_install_failure_case

echo "PASS prepared-release selector service-state and failure-atomic recovery mocks."
