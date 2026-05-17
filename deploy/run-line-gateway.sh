#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hermes-line-wordpress-agent}"
ENV_FILE="${ENV_FILE:-/etc/hermes-line-wordpress-agent/line-gateway.env}"
export PYTHONDONTWRITEBYTECODE="${PYTHONDONTWRITEBYTECODE:-1}"

if [[ -r "$ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "$ENV_FILE"
  set +a
fi

cd "$APP_DIR"
exec "$APP_DIR/.venv/bin/hermes-line-gateway"
