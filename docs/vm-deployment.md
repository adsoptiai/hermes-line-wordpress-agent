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
  line-gateway.env
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

WordPress Application Passwords usually contain spaces, so quote them:

```env
WORDPRESS_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"
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

## LINE Gateway Service

The included gateway is optional. Use it when Hermes Agent does not already provide a LINE adapter.

Edit the private LINE env file:

```bash
sudo nano /etc/hermes-line-wordpress-agent/line-gateway.env
sudo chmod 600 /etc/hermes-line-wordpress-agent/line-gateway.env
```

The systemd unit reads this file before switching to the service user, so mode `0600` is fine for
the LINE gateway.

Install the example service:

```bash
sudo cp /etc/hermes-line-wordpress-agent/hermes-line-gateway.service.example \
  /etc/systemd/system/hermes-line-gateway.service
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-line-gateway
```

Expose the webhook through Nginx:

```nginx
location /line/webhook {
    proxy_pass http://127.0.0.1:8787/line/webhook;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Set the LINE Developers Console webhook URL to:

```text
https://your-domain.example.com/line/webhook
```

## Nginx And Application Passwords

When WordPress runs behind Nginx/PHP-FPM and HTTPS is terminated by a proxy or CDN, WordPress may
not see the request as SSL. Application Password authentication can then fail with `rest_not_logged_in`.

The WordPress PHP-FPM location should pass both headers:

```nginx
location ~ \.php$ {
    include snippets/fastcgi-php.conf;
    fastcgi_pass unix:/run/php/php8.1-fpm.sock;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    fastcgi_param HTTPS on;
    fastcgi_param HTTP_AUTHORIZATION $http_authorization;
    include fastcgi_params;
}
```

Run `nginx -t` before reloading Nginx.

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
