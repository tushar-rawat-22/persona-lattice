#!/usr/bin/env bash
# Disposable regression: a failed retained-symlink enumeration must not
# authorize a prepared release. Never invokes real preparation or host paths.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/deploy/linux/prepare-release.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/release"

# The ownership scan succeeds; only the subsequent symlink enumeration fails.
# No filesystem or service state outside the disposable fixture is accessed.
cat > "$TMP/bin/find" <<'STUB'
#!/usr/bin/env bash
case " $* " in
  *" -print0 "*) exit 74 ;;
  *) exit 0 ;;
esac
STUB
chmod +x "$TMP/bin/find"

# Execute the exact function extracted from production source, but not the
# root-only, networked release-preparation entrypoint.
python3 - "$SOURCE" "$TMP/harness.sh" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_text()
start = source.index("validate_retained_release_tree() {")
end = source.index("\n}\n", start) + 2
harness = (
    "#!/usr/bin/env bash\n"
    "set -euo pipefail\n"
    "fail() { printf 'REJECT: %s\\n' \"$1\" >&2; exit 1; }\n"
    + source[start:end]
    + "\nvalidate_retained_release_tree \"$1\" \"isolated release\"\n"
    + "printf 'authorized\\n' > \"$2\"\n"
)
pathlib.Path(sys.argv[2]).write_text(harness)
PY
bash -n "$TMP/harness.sh"

rc=0
PATH="$TMP/bin:$PATH" bash "$TMP/harness.sh" "$TMP/release" "$TMP/authorized" \
  > "$TMP/stdout" 2> "$TMP/stderr" || rc=$?

if [[ "$rc" -eq 0 || -e "$TMP/authorized" ]]; then
  echo "FAIL prepare-release symlink enumeration error authorized release (rc=$rc)" >&2
  exit 1
fi
grep -Fq 'retained symlink scan failed' "$TMP/stderr" || {
  echo "FAIL prepare-release did not report failed symlink enumeration" >&2
  cat "$TMP/stderr" >&2
  exit 1
}
echo "PASS prepare-release fails closed on symlink enumeration errors."
