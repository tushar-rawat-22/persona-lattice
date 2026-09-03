#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'PersonaLattice Linux host verification failed: %s\n' "$1" >&2
  exit 1
}

for command in curl git readlink ss systemctl; do
  command -v "$command" >/dev/null 2>&1 || fail "required command '$command' is unavailable"
done

ROOT="$(readlink -f /opt/persona-lattice/current)"
EXPECTED_SHA="${1:-$(git -C "$ROOT" rev-parse HEAD)}"
[[ "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected release must be a full lowercase Git SHA"
[[ "$(git -C "$ROOT" rev-parse HEAD)" == "$EXPECTED_SHA" ]] || fail "current release does not match expected SHA"

systemctl is-active --quiet persona-lattice.service || fail "persona-lattice.service is not active"
curl --disable --silent --show-error --fail --max-time 5 http://127.0.0.1:18000/health >/dev/null || fail "API health failed"
curl --disable --silent --show-error --fail --max-time 5 http://127.0.0.1:13000/api/health >/dev/null || fail "same-origin web/API health failed"

for port in 13000 18000; do
  listeners="$(ss -H -ltn "sport = :$port" || true)"
  [[ -n "$listeners" ]] || fail "port $port has no listener"
  if printf '%s\n' "$listeners" | awk '{print $4}' | grep -Ev '^(127\.0\.0\.1|\[::1\]):' >/dev/null; then
    fail "port $port is listening beyond loopback"
  fi
done

printf '%s\n' \
  "PersonaLattice Linux host verification passed." \
  "Release SHA: $EXPECTED_SHA" \
  "Web boundary: 127.0.0.1:13000" \
  "API boundary: 127.0.0.1:18000" \
  "Service: active"
