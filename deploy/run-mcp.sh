#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-/etc/hermes-line-wordpress-agent/env}"
APP_DIR="${APP_DIR:-/opt/hermes-line-wordpress-agent}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

exec "$APP_DIR/.venv/bin/hermes-wp-mcp"

