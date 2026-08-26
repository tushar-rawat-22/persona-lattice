#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/personalattice-python-selection.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

printf '#!/usr/bin/env bash\nexit 0\n' >"$TMP_DIR/python3.13"
printf '#!/usr/bin/env bash\nexit 1\n' >"$TMP_DIR/python3"
chmod +x "$TMP_DIR/python3.13" "$TMP_DIR/python3"

selected="$(PATH="$TMP_DIR:/usr/bin:/bin" bash "$ROOT/scripts/lc1_select_python.sh")"
[[ "$selected" == "$TMP_DIR/python3.13" ]]

if PERSONALATTICE_LC1_PYTHON="$TMP_DIR/python3" \
  PATH="$TMP_DIR:/usr/bin:/bin" \
  bash "$ROOT/scripts/lc1_select_python.sh" >/dev/null 2>&1; then
  printf 'unsupported explicit Python override was accepted\n' >&2
  exit 1
fi
