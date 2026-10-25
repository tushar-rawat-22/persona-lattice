#!/usr/bin/env bash
# Mocked systemd state regression. Never accesses a real retained database.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="$ROOT/deploy/linux/restore-offline.sh"
[[ -f "$WRAPPER" ]] || { echo "missing Linux restore wrapper" >&2; exit 2; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/release/scripts"
cat > "$TMP/bin/readlink" <<'STUB'
#!/usr/bin/env bash
[[ "$1" == '-f' && "$2" == '/opt/persona-lattice/current' ]] || exit 9
printf '%s\n' "$TEST_RELEASE_ROOT"
STUB
cat > "$TMP/bin/systemctl" <<'STUB'
#!/usr/bin/env bash
case "$1" in
  is-active) exit "${TEST_IS_ACTIVE_EXIT:-3}" ;;
  show)
    [[ "${TEST_SYSTEMCTL_UNAVAILABLE:-0}" == 0 ]] || exit 127
    case "$2" in
      --property=LoadState)
        [[ "${TEST_LOAD_EXIT:-0}" == 0 ]] || exit "$TEST_LOAD_EXIT"
        printf '%s\n' "${TEST_LOAD_STATE:-loaded}" ;;
      --property=ActiveState)
        [[ "${TEST_ACTIVITY_EXIT:-0}" == 0 ]] || exit "$TEST_ACTIVITY_EXIT"
        printf '%s\n' "${TEST_ACTIVE_STATE:-inactive}" ;;
      *) exit 8 ;;
    esac ;;
  *) exit 7 ;;
esac
STUB
cat > "$TMP/release/scripts/live_beta_restore.sh" <<'STUB'
#!/usr/bin/env bash
[[ $# -eq 2 && "$1" == "$TEST_FAKE_BACKUP" && "$2" == '--confirm-offline' ]] || exit 7
printf 'entered\n' >> "$TEST_RESTORE_SENTINEL"
STUB
chmod +x "$TMP/bin/readlink" "$TMP/bin/systemctl" "$TMP/release/scripts/live_beta_restore.sh"
export PATH="$TMP/bin:$PATH"
export TEST_RELEASE_ROOT="$TMP/release" TEST_RESTORE_SENTINEL="$TMP/restore.log"
export TEST_FAKE_BACKUP="$TMP/fake-backup.sqlite3"
[[ ! -e "$TEST_FAKE_BACKUP" ]] || { echo "mock backup path must not exist" >&2; exit 2; }
run_case() {
  local name="$1" allow="$2" load="$3" active="$4" isactive="$5" loadexit="$6" activeexit="$7" unavailable="$8"
  export TEST_LOAD_STATE="$load" TEST_ACTIVE_STATE="$active" TEST_IS_ACTIVE_EXIT="$isactive"
  export TEST_LOAD_EXIT="$loadexit" TEST_ACTIVITY_EXIT="$activeexit" TEST_SYSTEMCTL_UNAVAILABLE="$unavailable"
  rm -f "$TEST_RESTORE_SENTINEL"
  local rc=0
  bash "$WRAPPER" "$TMP/fake-backup.sqlite3" >"$TMP/stdout" 2>"$TMP/stderr" || rc=$?
  if [[ "$allow" == yes ]]; then
    [[ "$rc" == 0 && -f "$TEST_RESTORE_SENTINEL" && "$(grep -c '^entered$' "$TEST_RESTORE_SENTINEL")" == 1 ]] || {
      printf 'FAIL %s expected single mocked restore (rc=%s)\n' "$name" "$rc" >&2; exit 1;
    }
  else
    [[ "$rc" != 0 && ! -e "$TEST_RESTORE_SENTINEL" ]] || {
      printf 'FAIL %s rejected state entered restore (rc=%s)\n' "$name" "$rc" >&2; exit 1;
    }
  fi
  printf 'PASS %s\n' "$name"
}
run_case loaded-inactive yes loaded inactive 3 0 0 0
run_case loaded-active no loaded active 0 0 0 0
run_case loaded-failed no loaded failed 3 0 0 0
run_case loaded-activating no loaded activating 3 0 0 0
run_case loaded-deactivating no loaded deactivating 3 0 0 0
run_case loaded-reloading no loaded reloading 3 0 0 0
run_case loaded-unknown no loaded unknown 3 0 0 0
run_case missing-inactive no not-found inactive 3 0 0 0
run_case masked-inactive no masked inactive 3 0 0 0
run_case load-query-error no loaded inactive 3 1 0 0
run_case activity-query-error no loaded inactive 3 0 1 0
run_case systemd-unavailable no loaded inactive 3 0 0 1
run_case active-status-conflict no loaded inactive 0 0 0 0
echo 'PASS 13/13 mocked service-state scenarios; no rejected restore entered.'
