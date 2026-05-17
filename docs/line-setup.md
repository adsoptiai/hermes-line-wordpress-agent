# LINE Setup

Hermes Agent should own the LINE gateway. This framework only provides the WordPress tools and
workflow guidance that Hermes calls after a LINE message is accepted.

## Recommended Flow

```text
LINE webhook
  -> Hermes LINE adapter
  -> allowed user/group check
  -> Hermes Agent session
  -> WordPress MCP tools
```

## Environment

Keep LINE secrets outside this repo:

```env
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_ALLOWED_USER_IDS=
LINE_ALLOWED_GROUP_IDS=
```

## UX Rules

- Reply quickly with "received" for tasks expected to exceed a few seconds.
- Do not depend on reply tokens for long tasks.
- Use approval buttons/postbacks for publish, schedule, delete, and homepage changes.
- Include post title, status, preview URL, and changed fields in approval messages.

## Command Examples

```text
Create an SEO draft about vector databases for Taiwanese enterprise teams.
Update the homepage hero copy, but show me the diff before applying.
Every Monday at 09:00, generate one draft article about data engineering.
Generate a featured image for post 123 and upload it to WordPress.
```

