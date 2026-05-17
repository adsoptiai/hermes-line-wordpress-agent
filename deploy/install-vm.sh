#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hermes-line-wordpress-agent}"
CONFIG_DIR="${CONFIG_DIR:-/etc/hermes-line-wordpress-agent}"
WP_DIR="${WP_DIR:-/var/www/wordpress}"
SERVICE_USER="${SERVICE_USER:-hermeswp}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root or through sudo." >&2
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip git rsync

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

mkdir -p "$APP_DIR" "$CONFIG_DIR"

rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude ".local" \
  --exclude "__pycache__" \
  ./ "$APP_DIR"/

cd "$APP_DIR"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e .
chmod 0755 deploy/run-mcp.sh
chmod 0755 deploy/run-line-gateway.sh

if [[ ! -f "$CONFIG_DIR/env" ]]; then
  install -m 0600 deploy/hermes-wordpress-mcp.env.example "$CONFIG_DIR/env"
fi

if [[ ! -f "$CONFIG_DIR/line-gateway.env" ]]; then
  install -m 0600 deploy/hermes-line-gateway.env.example "$CONFIG_DIR/line-gateway.env"
fi

if [[ ! -f "$CONFIG_DIR/site.profile.yaml" ]]; then
  install -m 0644 config/site.profile.example.yaml "$CONFIG_DIR/site.profile.yaml"
fi

if [[ ! -f "$CONFIG_DIR/policy.yaml" ]]; then
  install -m 0644 config/policy.example.yaml "$CONFIG_DIR/policy.yaml"
fi

install -m 0644 deploy/hermes-mcp-config.vm.example.json "$CONFIG_DIR/hermes-mcp-config.json"
install -m 0644 deploy/hermes-line-gateway.service.example \
  "$CONFIG_DIR/hermes-line-gateway.service.example"

if [[ -d "$WP_DIR/wp-content/plugins" ]]; then
  mkdir -p "$WP_DIR/wp-content/plugins/hermes-agent-bridge"
  install -m 0644 \
    wordpress-plugin/hermes-agent-bridge/hermes-agent-bridge.php \
    "$WP_DIR/wp-content/plugins/hermes-agent-bridge/hermes-agent-bridge.php"
  chown -R www-data:www-data "$WP_DIR/wp-content/plugins/hermes-agent-bridge"

  if command -v wp >/dev/null 2>&1; then
    sudo -u www-data wp --path="$WP_DIR" plugin activate hermes-agent-bridge || true
  fi
fi

chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
chmod 0755 "$APP_DIR"

cat <<EOF
Installed Hermes LINE WordPress Agent.

App directory:
  $APP_DIR

Config directory:
  $CONFIG_DIR

Next steps:
  1. Edit $CONFIG_DIR/env with WordPress credentials and bridge token.
  2. Add $CONFIG_DIR/hermes-mcp-config.json to Hermes Agent's MCP config.
  3. Edit $CONFIG_DIR/line-gateway.env with LINE credentials and allowlists.
  4. Install $CONFIG_DIR/hermes-line-gateway.service.example as a systemd service if needed.
  5. Restart the Hermes Agent/LINE gateway process.

Smoke test:
  set -a && . $CONFIG_DIR/env && set +a
  $APP_DIR/.venv/bin/hermes-wp-policy-check wp_create_post '{"status":"publish"}'
EOF
