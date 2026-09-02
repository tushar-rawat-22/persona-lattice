#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY="$ROOT/scripts/live_beta_verify_release.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/personalattice-verify-release-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin"
cat >"$TMP/bin/curl" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
headers=""
output=""
write_out=""
url=""
while (($#)); do
  case "$1" in
    -D) headers="$2"; shift 2 ;;
    -o) output="$2"; shift 2 ;;
    -w) write_out="$2"; shift 2 ;;
    --max-time) shift 2 ;;
    --disable|--silent|--show-error|--fail) shift ;;
    http*) url="$1"; shift ;;
    *) echo "unexpected fake curl argument: $1" >&2; exit 91 ;;
  esac
done
[[ -n "$headers" && -n "$output" && -n "$url" ]] || exit 92
if [[ "$url" == */api/v1/auth/session ]]; then
  status="${FAKE_AUTH_STATUS:-401}"
  {
    printf 'HTTP/2 %s\r\n' "$status"
    printf 'content-type: application/json\r\n'
    if [[ "${FAKE_AUTH_SET_COOKIE:-0}" == "1" ]]; then
      printf 'set-cookie: unexpected=1\r\n'
    fi
    printf '\r\n'
  } >"$headers"
  printf '{"detail":"Not authenticated"}' >"$output"
  [[ -z "$write_out" ]] || printf '%s' "$status"
else
  case "${FAKE_RELEASE_HEADER_CASE:-mixed}" in
    lower) release_header='x-personalattice-release' ;;
    upper) release_header='X-PERSONALATTICE-RELEASE' ;;
    mixed) release_header='X-PersonaLattice-Release' ;;
    *) echo "unexpected FAKE_RELEASE_HEADER_CASE" >&2; exit 93 ;;
  esac
  {
    printf 'HTTP/2 200\r\n'
    printf '%s: %s\r\n' "$release_header" "${FAKE_RELEASE_SHA:?}"
    printf 'Strict-Transport-Security: max-age=31536000\r\n'
    printf 'X-Content-Type-Options: nosniff\r\n'
    printf 'X-Frame-Options: DENY\r\n'
    printf '\r\n'
  } >"$headers"
  : >"$output"
fi
SH
chmod +x "$TMP/bin/curl"

EXPECTED_SHA="0123456789abcdef0123456789abcdef01234567"
export PATH="$TMP/bin:$PATH"
export FAKE_RELEASE_SHA="$EXPECTED_SHA"

for header_case in mixed lower upper; do
  export FAKE_RELEASE_HEADER_CASE="$header_case"
  output="$(bash "$VERIFY" 'https://private.example.test/' "$EXPECTED_SHA")"
  grep -Fq 'Release SHA: 0123456789abcdef0123456789abcdef01234567' <<<"$output"
  grep -Fq 'Unauthenticated session boundary: HTTP 401' <<<"$output"
done
unset FAKE_RELEASE_HEADER_CASE

export FAKE_AUTH_STATUS=200
if bash "$VERIFY" 'https://private.example.test' "$EXPECTED_SHA" >"$TMP/status.out" 2>"$TMP/status.err"; then
  echo 'expected HTTP 200 unauthenticated probe to fail' >&2
  exit 1
fi
grep -Fq 'expected 401' "$TMP/status.err"
unset FAKE_AUTH_STATUS

export FAKE_AUTH_SET_COOKIE=1
if bash "$VERIFY" 'https://private.example.test' "$EXPECTED_SHA" >"$TMP/cookie.out" 2>"$TMP/cookie.err"; then
  echo 'expected unauthenticated Set-Cookie to fail' >&2
  exit 1
fi
grep -Fq 'unexpectedly set a cookie' "$TMP/cookie.err"
unset FAKE_AUTH_SET_COOKIE

export FAKE_RELEASE_SHA="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
if bash "$VERIFY" 'https://private.example.test' "$EXPECTED_SHA" >"$TMP/sha.out" 2>"$TMP/sha.err"; then
  echo 'expected mismatched release SHA to fail' >&2
  exit 1
fi
grep -Fq 'expected 0123456789abcdef0123456789abcdef01234567' "$TMP/sha.err"

printf 'PersonaLattice stable release verification contract tests passed.\n'
