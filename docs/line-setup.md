# LINE Setup

Hermes Agent can own the LINE gateway directly. If your Hermes install does not include a LINE
adapter, this framework provides a small FastAPI gateway that accepts LINE webhooks, verifies the
LINE signature, invokes Hermes Agent, and returns the result through LINE.

## Recommended Flow

```text
LINE webhook
  -> Hermes LINE adapter or hermes-line-gateway
  -> allowed user/group check
  -> Hermes Agent session
  -> WordPress MCP tools
```

## Environment

Keep LINE secrets outside this repo. On a VM, use
`/etc/hermes-line-wordpress-agent/line-gateway.env`:

```env
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_ALLOWED_USER_IDS=
LINE_ALLOWED_GROUP_IDS=
LINE_ALLOWED_ROOM_IDS=
LINE_REQUIRE_ALLOWLIST=true
LINE_REPLY_MODE=ack_then_push
LINE_LOADING_ENABLED=true
LINE_LOADING_SECONDS=60
LINE_LOADING_SKIP_ACK=true

HERMES_BIN=/home/ubuntu/.local/bin/hermes
HERMES_MODEL=kimi-k2.6:cloud
HERMES_PROVIDER=custom
HERMES_TOOLSETS=wordpress
HERMES_WORKDIR=/home/ubuntu
```

## Run Locally

```bash
set -a && . .env && set +a
hermes-line-gateway
```

The default webhook URL is:

```text
https://your-domain.example.com/line/webhook
```

For setup, send `/whoami` to the LINE Official Account. The gateway replies with the LINE
`userId`, `groupId`, or `roomId` that you can place in the allowlist.

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

## Notes From LINE Messaging API

- Verify `x-line-signature` against the raw request body before parsing JSON.
- Reply messages use the `replyToken` received from a webhook event.
- Long-running Hermes tasks should use `LINE_REPLY_MODE=ack_then_push`: reply immediately with
  the token, then push the final result when Hermes finishes.
- Loading animation uses `POST /v2/bot/chat/loading/start`. LINE only displays it in one-on-one
  chats, not group chats or multi-person chats. If `LINE_LOADING_SKIP_ACK=true`, the gateway skips
  the immediate ack message in one-on-one chats so the loading animation stays visible until the
  final push message arrives.

Reference:

- LINE webhook signature verification: https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/
- LINE reply and push messages: https://developers.line.biz/en/docs/messaging-api/sending-messages/
