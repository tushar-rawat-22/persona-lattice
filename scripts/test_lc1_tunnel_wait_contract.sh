#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED='wait_for_url "$PUBLIC_URL/api/health" 600'

for script in lc1_host_acceptance.sh lc1_browser_hold.sh; do
  matches="$(grep -Fc "$EXPECTED" "$ROOT/scripts/$script")"
  if [[ "$matches" != "1" ]]; then
    printf '%s must allow the bounded five-minute Quick Tunnel readiness window\n' "$script" >&2
    exit 1
  fi
done
