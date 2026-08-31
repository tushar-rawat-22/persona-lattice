#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/live_beta_tunnel.sh"

[[ -f "$SCRIPT" ]]
bash -n "$SCRIPT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/cloudflared"

CREDENTIALS="$TMP/cloudflared/tunnel.json"
CONFIG="$TMP/cloudflared/config.yml"
printf '{"AccountTag":"test","TunnelSecret":"redacted","TunnelID":"00000000-0000-0000-0000-000000000000"}\n' >"$CREDENTIALS"
chmod 600 "$CREDENTIALS"

cat >"$CONFIG" <<EOF
 tunnel: 00000000-0000-0000-0000-000000000000
 credentials-file: $CREDENTIALS
 ingress:
   - hostname: admin.example.test
     service: http://127.0.0.1:13000
   - service: http_status:404
EOF

cat >"$TMP/bin/cloudflared" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$*" == *"tunnel ingress validate"* ]]; then
  exit 0
fi
if [[ "$*" == *"tunnel ingress rule https://admin.example.test"* ]]; then
  printf 'Matched rule #0\n\thostname: admin.example.test\n\tservice: %s\n' "${FAKE_RULE_TARGET:-http://127.0.0.1:13000}"
  exit 0
fi
if [[ "$*" == *"tunnel ingress rule https://persona-lattice-unmatched.invalid"* ]]; then
  printf 'Matched rule #1\n\tservice: %s\n' "${FAKE_CATCHALL_TARGET:-http_status:404}"
  exit 0
fi
if [[ "$*" == *"tunnel run"* ]]; then
  printf 'fake tunnel run\n'
  exit 0
fi
printf 'unexpected cloudflared invocation: %s\n' "$*" >&2
exit 91
EOF
chmod +x "$TMP/bin/cloudflared"

run_preflight() {
  PATH="$TMP/bin:$PATH" \
  PERSONALATTICE_CLOUDFLARED_CONFIG="$CONFIG" \
  PERSONALATTICE_PRIVATE_HOSTNAME='admin.example.test' \
  PERSONALATTICE_LIVE_WEB_PORT='13000' \
  PERSONALATTICE_LIVE_API_PORT='18000' \
    bash "$SCRIPT" preflight
}

output="$(run_preflight)"
printf '%s\n' "$output" | grep -F -- 'PersonaLattice named-tunnel preflight passed.' >/dev/null
printf '%s\n' "$output" | grep -F -- 'Origin:   http://127.0.0.1:13000' >/dev/null
printf '%s\n' "$output" | grep -F -- 'API port 18000 is not published' >/dev/null

if FAKE_RULE_TARGET='http://127.0.0.1:18000' run_preflight >/dev/null 2>"$TMP/wrong-origin.err"; then
  echo 'tunnel preflight accepted API-port routing' >&2
  exit 1
fi
grep -F -- 'private hostname must map exactly to service: http://127.0.0.1:13000' "$TMP/wrong-origin.err" >/dev/null

if FAKE_CATCHALL_TARGET='http://127.0.0.1:13000' run_preflight >/dev/null 2>"$TMP/no-catchall.err"; then
  echo 'tunnel preflight accepted a non-404 catch-all' >&2
  exit 1
fi
grep -F -- 'fail-closed 404 catch-all' "$TMP/no-catchall.err" >/dev/null

chmod 644 "$CREDENTIALS"
if run_preflight >/dev/null 2>"$TMP/credentials-mode.err"; then
  echo 'tunnel preflight accepted non-owner-only credentials' >&2
  exit 1
fi
grep -F -- 'tunnel credentials file must be owner-only' "$TMP/credentials-mode.err" >/dev/null
chmod 600 "$CREDENTIALS"

cat >"$CONFIG" <<EOF
 tunnel: 00000000-0000-0000-0000-000000000000
 credentials-file: $CREDENTIALS
 ingress:
   - hostname: admin.example.test
     service: http://127.0.0.1:13000
   - hostname: accidental-api.example.test
     service: http://127.0.0.1:18000
   - service: http_status:404
EOF
if run_preflight >/dev/null 2>"$TMP/api-route.err"; then
  echo 'tunnel preflight accepted config containing API ingress' >&2
  exit 1
fi
grep -F -- 'must never target the private API port 18000' "$TMP/api-route.err" >/dev/null

if grep -F -- 'cloudflared tunnel --url' "$SCRIPT" >/dev/null; then
  echo 'stable private-beta tunnel helper must not create a Quick Tunnel' >&2
  exit 1
fi

printf 'live-beta named-tunnel contract passed\n'
