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

BASE_URL="${URL%/}"
HEADERS="$(mktemp "${TMPDIR:-/tmp}/personalattice-release-headers.XXXXXX")"
AUTH_HEADERS="$(mktemp "${TMPDIR:-/tmp}/personalattice-auth-headers.XXXXXX")"
AUTH_BODY="$(mktemp "${TMPDIR:-/tmp}/personalattice-auth-body.XXXXXX")"
trap 'rm -f "$HEADERS" "$AUTH_HEADERS" "$AUTH_BODY"' EXIT

# --disable prevents a user-level curl config from injecting credentials, cookies,
# headers or redirect behavior into release evidence.
curl --disable --silent --show-error --fail --max-time 15 \
  -D "$HEADERS" -o /dev/null "$BASE_URL/"

# HTTP header field names are case-insensitive. Avoid awk's non-portable IGNORECASE
# extension so this verifier behaves the same with macOS/BSD awk and GNU awk.
actual_sha="$(awk -F ':' '
  tolower($1) == "x-personalattice-release" {
    value = $0
    sub(/^[^:]*:[[:space:]]*/, "", value)
    sub(/\r$/, "", value)
    print value
  }
' "$HEADERS" | tail -n 1)"
[[ -n "$actual_sha" ]] || fail "stable endpoint did not return X-PersonaLattice-Release"
[[ "$actual_sha" == "$EXPECTED_SHA" ]] || fail "stable endpoint serves $actual_sha, expected $EXPECTED_SHA"

grep -Eiq '^strict-transport-security:' "$HEADERS" || fail "stable endpoint is missing HSTS"
grep -Eiq '^x-content-type-options:[[:space:]]*nosniff' "$HEADERS" || fail "stable endpoint is missing nosniff"
grep -Eiq '^x-frame-options:[[:space:]]*DENY' "$HEADERS" || fail "stable endpoint is missing frame denial"

# Prove that the stable same-origin /api path reaches the authenticated API and
# fails closed when no session cookie is supplied. This intentionally sends no
# credentials and must never create a session as part of release verification.
auth_status="$(curl --disable --silent --show-error --max-time 15 \
  -D "$AUTH_HEADERS" -o "$AUTH_BODY" -w '%{http_code}' \
  "$BASE_URL/api/v1/auth/session")"
[[ "$auth_status" == "401" ]] || fail "unauthenticated same-origin session probe returned HTTP $auth_status, expected 401"
if grep -Eiq '^set-cookie:' "$AUTH_HEADERS"; then
  fail "unauthenticated session probe unexpectedly set a cookie"
fi

printf 'PersonaLattice stable private-beta release verified.\n'
printf 'URL: %s\n' "$BASE_URL"
printf 'Release SHA: %s\n' "$actual_sha"
printf 'Unauthenticated session boundary: HTTP 401\n'