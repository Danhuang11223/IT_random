#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  else
    echo "Python interpreter not found." >&2
    exit 1
  fi
fi

ADMIN_USERNAME="${DEMO_ADMIN_USERNAME:-admin}"
ADMIN_EMAIL="${DEMO_ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${DEMO_ADMIN_PASSWORD:-Admin123456!}"
DEMO_SKIP_ADMIN="${DEMO_SKIP_ADMIN:-0}"
DEMO_SKIP_SEED="${DEMO_SKIP_SEED:-0}"

CMD=(
  "$PYTHON_BIN" manage.py demo_reset
  --admin-username "$ADMIN_USERNAME"
  --admin-email "$ADMIN_EMAIL"
  --admin-password "$ADMIN_PASSWORD"
)

if [[ "$DEMO_SKIP_ADMIN" == "1" ]]; then
  CMD+=(--skip-admin)
fi

if [[ "$DEMO_SKIP_SEED" == "1" ]]; then
  CMD+=(--skip-seed)
fi

CMD+=("$@")
"${CMD[@]}"
