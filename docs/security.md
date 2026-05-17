# Security

This project is designed for agents that can modify production websites. Treat it as privileged
infrastructure.

## Required Controls

- Use a dedicated WordPress user.
- Store secrets in environment variables or a secret manager.
- Keep site profiles and brand rules in a private repo or ignored local config.
- Require approval for publish, delete, homepage, SEO settings, robots.txt, sitemap, and bulk edits.
- Restrict LINE user IDs and group IDs.
- Log all write operations with actor, prompt, post ID, changed fields, and approval state.

## Suggested Environment

```env
WP_ALLOWED_WRITE_TOOLS=wp_create_post,wp_update_post,wp_upload_media,wp_set_featured_image
WP_ALLOW_DESTRUCTIVE=false
REQUIRE_APPROVAL_FOR=publish,delete,homepage_update,seo_settings_update,bulk_update
```

## Never Commit

- LINE channel access token
- WordPress application password
- Bridge token
- Real LINE user IDs or group IDs
- Customer SEO strategy
- Private brand voice

