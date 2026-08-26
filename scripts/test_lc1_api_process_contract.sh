#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED='exec "$PYTHON" -m uvicorn app.main:app'

for script in lc1_host_acceptance.sh lc1_browser_hold.sh; do
  matches="$(grep -Fc "$EXPECTED" "$ROOT/scripts/$script")"
  if [[ "$matches" != "1" ]]; then
    printf '%s must track the Uvicorn process directly for reliable stop and cleanup\n' "$script" >&2
    exit 1
  fi
done
