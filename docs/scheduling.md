# Scheduling

Use Hermes Agent's scheduler or cron runner for recurring content operations. The WordPress MCP
server should remain stateless.

## Example Workflow

```text
Schedule:
  every Monday 09:00 Asia/Taipei

Task:
  1. Generate topic ideas from the site profile.
  2. Pick one approved content pillar.
  3. Draft the article.
  4. Generate or select an image.
  5. Upload the image to WordPress.
  6. Create a draft post.
  7. Send preview to LINE for approval.
```

## Default Policy

- Recurring tasks may create drafts without approval.
- Recurring tasks must not publish without approval.
- Generated images must have alt text before upload.
- Failed jobs should send a concise LINE notification with the job name and failure reason.

