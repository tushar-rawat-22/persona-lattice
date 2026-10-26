#!/usr/bin/env bash
# Disposable regression: an existing prepared release must never be deleted
# merely because release preparation is attempted again.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/deploy/linux/prepare-release.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/releases"
python3 - "$SOURCE" "$TMP/harness.sh" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_text()
start = source.index('RELEASE_DIR="$RELEASE_ROOT/$TARGET_SHA"\n')
end = source.index('\ngit -C "$RELEASE_DIR" remote set-url', start)
block = source[start:end]
harness = (
    '#!/usr/bin/env bash\nset -euo pipefail\n'
    'RELEASE_ROOT="$1/releases"\nCURRENT_LINK="$1/current"\n'
    'TARGET_SHA="$2"\nMOCK_GIT_LOG="$1/git-actions"\n'
    'REPOSITORY_URL="https://invalid.example.invalid/repo.git"\n'
    'fail() { printf "DENY: %s\\n" "$1" >&2; exit 1; }\n'
    'git() { printf "%s\\n" "$*" >> "$MOCK_GIT_LOG"; return 75; }\n'
    + block + '\n'
)
pathlib.Path(sys.argv[2]).write_text(harness)
PY
bash -n "$TMP/harness.sh"

target_sha="1111111111111111111111111111111111111111"
prior_sha="2222222222222222222222222222222222222222"
mkdir -p "$TMP/releases/$target_sha" "$TMP/releases/$prior_sha"
printf 'previously prepared release evidence\n' > "$TMP/releases/$target_sha/retained-marker"
ln -s "$TMP/releases/$prior_sha" "$TMP/current"
rc=0
bash "$TMP/harness.sh" "$TMP" "$target_sha" > "$TMP/out" 2> "$TMP/err" || rc=$?
[[ "$rc" -ne 0 && -f "$TMP/releases/$target_sha/retained-marker" && ! -e "$TMP/git-actions" ]] || {
  echo "FAIL existing-prepared-release was deleted or re-prepared (rc=$rc)" >&2
  exit 1
}
echo "PASS existing prepared release preserved on refused re-preparation"

# The active release is also immutable, with no attempt to clone.
rm -f "$TMP/current"
ln -s "$TMP/releases/$target_sha" "$TMP/current"
rc=0
bash "$TMP/harness.sh" "$TMP" "$target_sha" > "$TMP/out" 2> "$TMP/err" || rc=$?
[[ "$rc" -ne 0 && -f "$TMP/releases/$target_sha/retained-marker" && ! -e "$TMP/git-actions" ]] || {
  echo "FAIL active-prepared-release was mutated or re-prepared (rc=$rc)" >&2
  exit 1
}
echo "PASS active prepared release preserved"

# A genuinely absent release still reaches the ordinary clone path.
new_sha="3333333333333333333333333333333333333333"
rc=0
bash "$TMP/harness.sh" "$TMP" "$new_sha" > "$TMP/out" 2> "$TMP/err" || rc=$?
[[ "$rc" -ne 0 && -f "$TMP/git-actions" ]] || {
  echo "FAIL new release did not reach the ordinary preparation path" >&2
  exit 1
}
echo "PASS new release preparation path remains available"
