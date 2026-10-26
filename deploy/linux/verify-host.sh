#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'PersonaLattice Linux host verification failed: %s\n' "$1" >&2
  exit 1
}

for command in awk curl git readlink ss systemctl; do
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
  if ! listeners="$(ss -H -ltn "sport = :$port")"; then
    fail "cannot complete listener inspection for port $port"
  fi
  [[ -n "$listeners" ]] || fail "port $port has no listener"
  # Check every returned listener and the parser's exit status. A failed awk
  # must not be mistaken for "no unsafe listener matched".
  if ! printf '%s\n' "$listeners" | awk '
    NF < 4 { exit 1 }
    $4 !~ /^(127[.]0[.]0[.]1|\[::1\]):/ { exit 1 }
  '; then
    fail "port $port is listening beyond loopback or listener inspection failed"
  fi
done

printf '%s\n' \
  "PersonaLattice Linux host verification passed." \
  "Release SHA: $EXPECTED_SHA" \
  "Web boundary: 127.0.0.1:13000" \
  "API boundary: 127.0.0.1:18000" \
  "Service: active"
