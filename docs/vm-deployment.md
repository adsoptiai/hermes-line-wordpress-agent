# VM Deployment

This framework is designed to run on the same VM as Hermes Agent and WordPress.

The WordPress MCP server uses stdio transport, so it is usually spawned by Hermes Agent from an MCP
config. It should not be exposed as a public HTTP service.

## Target Layout

```text
/opt/hermes-line-wordpress-agent/
  .venv/
  src/
  skills/
  wordpress-plugin/

/etc/hermes-line-wordpress-agent/
  env
  site.profile.yaml
  policy.yaml
  hermes-mcp-config.json

/var/www/wordpress/
  wp-content/plugins/hermes-agent-bridge/
```

## Install

On the VM:

```bash
git clone https://github.com/adsoptiai/hermes-line-wordpress-agent.git
cd hermes-line-wordpress-agent
sudo bash deploy/install-vm.sh
```

Edit the private env file:

```bash
sudo nano /etc/hermes-line-wordpress-agent/env
sudo chmod 600 /etc/hermes-line-wordpress-agent/env
```

Copy or create the private site profile and policy:

```bash
sudo cp config/site.profile.example.yaml /etc/hermes-line-wordpress-agent/site.profile.yaml
sudo cp config/policy.example.yaml /etc/hermes-line-wordpress-agent/policy.yaml
sudo nano /etc/hermes-line-wordpress-agent/site.profile.yaml
sudo nano /etc/hermes-line-wordpress-agent/policy.yaml
```

## Register With Hermes

Merge `/etc/hermes-line-wordpress-agent/hermes-mcp-config.json` into the Hermes Agent MCP config.

The config uses `/opt/hermes-line-wordpress-agent/deploy/run-mcp.sh`, which loads
`/etc/hermes-line-wordpress-agent/env` before starting the stdio MCP server.

Restart Hermes/LINE gateway after updating the MCP config.

## Smoke Tests

Policy check:

```bash
set -a && . /etc/hermes-line-wordpress-agent/env && set +a
/opt/hermes-line-wordpress-agent/.venv/bin/hermes-wp-policy-check wp_create_post '{"status":"publish"}'
```

Python import:

```bash
/opt/hermes-line-wordpress-agent/.venv/bin/python -m compileall /opt/hermes-line-wordpress-agent/src
```

WordPress plugin:

```bash
curl -H "X-Hermes-Bridge-Token: $WORDPRESS_BRIDGE_TOKEN" \
  "$WORDPRESS_BASE_URL/wp-json/hermes-agent/v1/health"
```

## Security

- Keep `/etc/hermes-line-wordpress-agent/env` mode `0600`.
- Keep MCP stdio local to the VM.
- Do not expose the MCP process behind Nginx.
- Use a dedicated WordPress user and Application Password.
- Require approval for publish, delete, homepage, SEO settings, and bulk changes.
