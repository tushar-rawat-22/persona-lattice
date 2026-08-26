#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${PERSONALATTICE_LC1_PYTHON:-}" ]]; then
  candidates=("$PERSONALATTICE_LC1_PYTHON")
else
  candidates=(python3.13 python3.12 python3.11 python3 python)
fi

for candidate in "${candidates[@]}"; do
  resolved="$(command -v "$candidate" 2>/dev/null || true)"
  [[ -n "$resolved" ]] || continue
  if "$resolved" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' \
    >/dev/null 2>&1; then
    printf '%s\n' "$resolved"
    exit 0
  fi
done

printf 'PersonaLattice LC1 requires Python 3.11 or newer. Set PERSONALATTICE_LC1_PYTHON to a supported interpreter.\n' >&2
exit 1
