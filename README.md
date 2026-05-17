# Hermes LINE WordPress Agent

Reusable framework for operating WordPress sites from Hermes Agent through LINE:

- LINE messages are handled by Hermes Agent's LINE gateway.
- This repo includes a small LINE webhook gateway for deployments where Hermes Agent does not
  already provide a LINE adapter.
- WordPress operations are exposed as MCP tools.
- SEO article, image post, and editor workflows are packaged as skills.
- Publish, delete, homepage, and SEO-setting changes can require explicit approval.
- Site-specific profiles live outside this repo in ignored local config.

This repository is intentionally generic. Do not commit client/site secrets, LINE user IDs,
brand strategy, or production WordPress credentials.

## Architecture

```text
LINE user/group
  -> Hermes LINE gateway
  -> Hermes Agent session
  -> WordPress MCP tools
  -> WordPress REST API + optional companion plugin
```

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env
```

Register the MCP server in your Hermes or MCP client config:

```json
{
  "mcpServers": {
    "wordpress": {
      "command": "hermes-wp-mcp",
      "env": {
        "WORDPRESS_BASE_URL": "https://cms.example.com",
        "WORDPRESS_USERNAME": "editor",
        "WORDPRESS_APP_PASSWORD": "xxxx xxxx xxxx xxxx xxxx xxxx",
        "WORDPRESS_BRIDGE_TOKEN": "optional-shared-token"
      }
    }
  }
}
```

Run the optional LINE webhook gateway:

```bash
export LINE_CHANNEL_SECRET=...
export LINE_CHANNEL_ACCESS_TOKEN=...
export HERMES_TOOLSETS=wordpress
hermes-line-gateway
```

Webhook endpoint:

```text
POST /line/webhook
```

## What Goes Where

Open-source repo:

- Generic WordPress tools
- Example config
- Skills and workflow prompts
- Companion plugin source
- Deployment templates

Private/local repo:

- Real WordPress URLs and credentials
- LINE allowlists
- Brand voice
- SEO strategy
- Publishing schedule
- Client-specific rules

## Private Site Integration

Create a private site config outside Git, for example:

```bash
mkdir -p .local/my-site
cp config/site.profile.example.yaml .local/my-site/site.profile.yaml
cp config/policy.example.yaml .local/my-site/policy.yaml
```

Then set:

```bash
SITE_PROFILE_PATH=.local/my-site/site.profile.yaml
POLICY_PATH=.local/my-site/policy.yaml
```

The `.local/` directory is ignored by this repo.

## Tools

The MCP server exposes:

- `wp_get_post`
- `wp_search_posts`
- `wp_create_post`
- `wp_update_post`
- `wp_schedule_post`
- `wp_upload_media`
- `wp_set_featured_image`
- `wp_get_preview_url`
- `wp_set_seo_meta`
- `wp_health`

## Documentation

- [Architecture](docs/architecture.md)
- [LINE setup](docs/line-setup.md)
- [WordPress setup](docs/wordpress-setup.md)
- [Scheduling](docs/scheduling.md)
- [Security](docs/security.md)
- [VM deployment](docs/vm-deployment.md)
