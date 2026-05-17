---
name: wordpress-editor
description: Use when editing WordPress pages, posts, custom post types, media, or SEO metadata through Hermes Agent.
---

# WordPress Editor Skill

## Rules

- Read existing content before editing.
- Prefer drafts and previews over direct publishing.
- For public changes, present a concise change summary and request approval.
- Never delete, publish, schedule, or update homepage/SEO settings without approval.
- Preserve existing shortcodes, embeds, block comments, and custom HTML unless the user asks to change them.

## Workflow

1. Identify the post/page/custom post type and ID.
2. Fetch the current content with `wp_get_post`.
3. Produce a short plan and identify risky changes.
4. Apply non-public changes with `wp_update_post`.
5. Return the preview URL with `wp_get_preview_url`.

## Approval Message Shape

```text
Proposed WordPress change:
Title:
Target:
Status:
Changed fields:
Preview:

Reply approve to apply.
```

