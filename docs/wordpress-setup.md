# WordPress Setup

## Application Passwords

Create a dedicated WordPress user with the minimum role required for your workflow, then generate an
Application Password from the user profile screen.

Use these environment variables:

```env
WORDPRESS_BASE_URL=https://cms.example.com
WORDPRESS_USERNAME=editor
WORDPRESS_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"
```

## REST API

The MCP server uses core WordPress REST endpoints:

- `/wp-json/wp/v2/posts`
- `/wp-json/wp/v2/pages`
- `/wp-json/wp/v2/media`
- `/wp-json/wp/v2/users/me`

Custom post types must have `show_in_rest` enabled.

If REST requests using Application Passwords return `rest_not_logged_in`, check that Nginx/PHP-FPM
passes `HTTP_AUTHORIZATION` to WordPress and that WordPress sees the request as HTTPS.

## SEO Meta

Core WordPress does not provide a universal SEO meta API. For Yoast, Rank Math, AIOSEO, or custom
schema fields, install the optional companion plugin in `wordpress-plugin/hermes-agent-bridge`.

The companion plugin exposes:

```text
GET  /wp-json/hermes-agent/v1/health
POST /wp-json/hermes-agent/v1/seo-meta/<post_id>
```

Protect it with both WordPress Application Password auth and `WORDPRESS_BRIDGE_TOKEN`.
