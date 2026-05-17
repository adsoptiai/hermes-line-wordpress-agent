---
name: image-post
description: Use when generating, editing, uploading, or assigning WordPress images for posts or pages.
---

# Image Post Skill

## Rules

- Always write useful alt text.
- Keep generated image prompts aligned to the site's brand rules.
- Upload only final candidate images.
- Do not replace a featured image without stating the current and new media IDs.

## Workflow

1. Create the image prompt or select a local file.
2. Generate or edit the image through the configured media tool.
3. Upload with `wp_upload_media`.
4. Set featured image with `wp_set_featured_image` when requested.
5. Return media ID, URL, and alt text.

