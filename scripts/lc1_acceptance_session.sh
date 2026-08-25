#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash scripts/lc1_host_acceptance.sh

printf '\nAutomated host acceptance passed. Starting browser hold against the exact tested commit.\n'
exec bash scripts/lc1_browser_hold.sh
