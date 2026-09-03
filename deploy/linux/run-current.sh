#!/usr/bin/env bash
set -euo pipefail

ROOT="$(readlink -f /opt/persona-lattice/current)"
ENV_FILE="/etc/persona-lattice/production.env"
STATE_ROOT="/var/lib/persona-lattice"

fail() {
  printf 'PersonaLattice Linux runtime failed: %s\n' "$1" >&2
  exit 1
}

[[ -d "$ROOT/.git" ]] || fail "current release is not a Git checkout: $ROOT"
RELEASE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
[[ "$RELEASE_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "current release is not a full Git SHA"

export PERSONALATTICE_PRODUCTION_ENV_FILE="$ENV_FILE"
export PERSONALATTICE_LIVE_RUNTIME_DIR="$STATE_ROOT/runtime/$RELEASE_SHA"
export PERSONALATTICE_LIVE_VENV="$PERSONALATTICE_LIVE_RUNTIME_DIR/venv"
export PERSONALATTICE_LIVE_API_PORT=18000
export PERSONALATTICE_LIVE_WEB_PORT=13000

exec bash "$ROOT/scripts/live_beta_start.sh" --run-prepared
