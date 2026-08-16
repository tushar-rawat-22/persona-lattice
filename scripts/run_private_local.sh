#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$ROOT/services/api"
WEB_DIR="$ROOT/apps/web"
VENV="$ROOT/.venv-personalattice"
CONFIG_DIR="$HOME/.config/persona-lattice"
DATA_DIR="$HOME/.local/share/persona-lattice"
ENV_FILE="$CONFIG_DIR/local.env"

mkdir -p "$CONFIG_DIR" "$DATA_DIR"
chmod 700 "$CONFIG_DIR" "$DATA_DIR"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[PersonaLattice] Creating local Python environment..."
  python3 -m venv "$VENV"
fi

echo "[PersonaLattice] Installing/updating API dependencies..."
"$VENV/bin/python" -m pip install -q -e "$API_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "[PersonaLattice] First-run admin setup. Nothing plaintext will be written to disk."
  read -r -p "Admin username [admin]: " ADMIN_USERNAME
  ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
  export PYTHONPATH="$API_DIR"
  PASSWORD_HASH="$("$VENV/bin/python" - <<'PY'
from getpass import getpass
from app.admin_auth import hash_admin_password

first = getpass("Admin password (12+ characters): ")
second = getpass("Confirm admin password: ")
if first != second:
    raise SystemExit("Passwords do not match.")
print(hash_admin_password(first))
PY
)"
  umask 077
  cat > "$ENV_FILE" <<EOF
PERSONALATTICE_ADMIN_USERNAME='$ADMIN_USERNAME'
PERSONALATTICE_ADMIN_PASSWORD_HASH='$PASSWORD_HASH'
PERSONALATTICE_SESSION_SECONDS='28800'
PERSONALATTICE_COOKIE_SECURE='false'
PERSONALATTICE_SESSION_COOKIE='personalattice_session'
PERSONALATTICE_DB_PATH='$DATA_DIR/personalattice.db'
PERSONALATTICE_CASE_RETENTION_DAYS='30'
EOF
  chmod 600 "$ENV_FILE"
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [ ! -d "$WEB_DIR/node_modules" ]; then
  echo "[PersonaLattice] Installing web dependencies..."
  (cd "$WEB_DIR" && npm ci --no-audit --no-fund)
fi

cleanup() {
  echo
  echo "[PersonaLattice] Stopping local services..."
  kill "${API_PID:-}" "${WEB_PID:-}" 2>/dev/null || true
  wait "${API_PID:-}" "${WEB_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[PersonaLattice] Starting private API on 127.0.0.1:8000..."
"$VENV/bin/python" -m uvicorn app.main:app \
  --app-dir "$API_DIR" \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 1 > "$DATA_DIR/api.log" 2>&1 &
API_PID=$!

for _ in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "[PersonaLattice] API failed to start. Log: $DATA_DIR/api.log" >&2
    exit 1
  fi
  sleep 0.25
done

if ! curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "[PersonaLattice] API health check timed out. Log: $DATA_DIR/api.log" >&2
  exit 1
fi

echo "[PersonaLattice] Starting web app on 127.0.0.1:3000..."
(
  cd "$WEB_DIR"
  export NEXT_PUBLIC_API_URL=/api
  export PERSONALATTICE_API_ORIGIN=http://127.0.0.1:8000
  npm run dev -- --hostname 127.0.0.1
) > "$DATA_DIR/web.log" 2>&1 &
WEB_PID=$!

for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:3000/admin >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    echo "[PersonaLattice] Web app failed to start. Log: $DATA_DIR/web.log" >&2
    exit 1
  fi
  sleep 0.25
done

if ! curl -fsS http://127.0.0.1:3000/admin >/dev/null 2>&1; then
  echo "[PersonaLattice] Web health check timed out. Log: $DATA_DIR/web.log" >&2
  exit 1
fi

echo
printf '%s\n' \
  "PersonaLattice is running." \
  "Public preview: http://127.0.0.1:3000/" \
  "Private admin:  http://127.0.0.1:3000/admin" \
  "Case database:  $DATA_DIR/personalattice.db" \
  "Press Control-C here to stop both services."

if command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:3000/admin" || true
fi

wait "$API_PID" "$WEB_PID"
