#!/usr/bin/env bash
# Isolated loopback verifier regression. No real network listeners or host commands.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/deploy/linux/verify-host.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"

# Exercise the exact production port-listener loop, not a reimplementation.
python3 - "$SOURCE" "$TMP/verify-loopback.sh" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_text()
start_marker = "for port in 13000 18000; do\n"
end_marker = "\nprintf '%s\\n' \\\n  \"PersonaLattice Linux host verification passed.\""
if source.count(start_marker) != 1 or source.count(end_marker) != 1:
    raise SystemExit("production loopback verifier contract changed")
start = source.index(start_marker)
end = source.index(end_marker, start)
harness = (
    "#!/usr/bin/env bash\nset -euo pipefail\n"
    'fail() { printf "DENY: %s\\n" "$1" >&2; exit 1; }\n'
    + source[start:end] + "\n"
)
pathlib.Path(sys.argv[2]).write_text(harness)
PY
bash -n "$TMP/verify-loopback.sh"

cat > "$TMP/bin/ss" <<'STUB'
#!/usr/bin/env bash
[[ "$1" == -H && "$2" == -ltn && "$3" == "sport = :"* ]] || exit 99
port="${3##*:}"
case "${MOCK_SS_MODE:-loopback}" in
  loopback)
    printf 'LISTEN 0 128 127.0.0.1:%s 0.0.0.0:*\n' "$port" ;;
  partial-failure)
    # ss can emit a plausible partial listing before returning an error.
    printf 'LISTEN 0 128 127.0.0.1:%s 0.0.0.0:*\n' "$port"
    exit 74 ;;
  wildcard)
    printf 'LISTEN 0 128 0.0.0.0:%s 0.0.0.0:*\n' "$port" ;;
  missing) : ;;
  *) exit 99 ;;
esac
STUB
chmod +x "$TMP/bin/ss"
export PATH="$TMP/bin:$PATH"

run_case() {
  local name="$1" expected="$2" rc=0
  export MOCK_SS_MODE="$name"
  bash "$TMP/verify-loopback.sh" >"$TMP/stdout" 2>"$TMP/stderr" || rc=$?
  if [[ "$expected" == allow ]]; then
    [[ "$rc" -eq 0 ]] || {
      echo "FAIL $name rejected valid loopback listeners (rc=$rc)" >&2
      cat "$TMP/stderr" >&2
      exit 1
    }
  else
    [[ "$rc" -ne 0 ]] || {
      echo "FAIL $name accepted incomplete or unsafe listener evidence (rc=$rc)" >&2
      exit 1
    }
  fi
  echo "PASS $name"
}

run_case loopback allow
run_case wildcard deny
run_case missing deny
run_case partial-failure deny
echo "PASS Linux host loopback verification mocks."
