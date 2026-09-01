#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
EXPECTED_SHA="${2:-}"

fail() {
  printf 'PersonaLattice release verification failed: %s\n' "$1" >&2
  exit 1
}

[[ "$URL" == https://* ]] || fail "first argument must be the stable HTTPS private-beta URL"
[[ "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "second argument must be the full lowercase expected Git SHA"
command -v curl >/dev/null 2>&1 || fail "curl is unavailable"

HEADERS="$(mktemp "${TMPDIR:-/tmp}/personalattice-release-headers.XXXXXX")"
trap 'rm -f "$HEADERS"' EXIT

curl --silent --show-error --fail --max-time 15 -D "$HEADERS" -o /dev/null "$URL/"

actual_sha="$(awk 'BEGIN{IGNORECASE=1} /^X-PersonaLattice-Release:/ {gsub("\r", "", $2); print $2}' "$HEADERS" | tail -n 1)"
[[ -n "$actual_sha" ]] || fail "stable endpoint did not return X-PersonaLattice-Release"
[[ "$actual_sha" == "$EXPECTED_SHA" ]] || fail "stable endpoint serves $actual_sha, expected $EXPECTED_SHA"

grep -Eiq '^strict-transport-security:' "$HEADERS" || fail "stable endpoint is missing HSTS"
grep -Eiq '^x-content-type-options:[[:space:]]*nosniff' "$HEADERS" || fail "stable endpoint is missing nosniff"
grep -Eiq '^x-frame-options:[[:space:]]*DENY' "$HEADERS" || fail "stable endpoint is missing frame denial"

printf 'PersonaLattice stable private-beta release verified.\n'
printf 'URL: %s\n' "$URL"
printf 'Release SHA: %s\n' "$actual_sha"
