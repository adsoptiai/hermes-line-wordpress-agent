# Architecture

This project keeps the messaging surface, agent runtime, and WordPress operations separate.

```text
LINE Messaging API
  -> Hermes LINE gateway
  -> Hermes Agent
  -> MCP tool registry
  -> wordpress MCP server
  -> WordPress REST API
  -> optional hermes-agent-bridge plugin
```

## Boundaries

- LINE gateway handles webhook verification, reply tokens, push messages, and postbacks.
- Hermes Agent owns reasoning, skills, memory, long-running tasks, and schedules.
- This repo owns WordPress tools, approval policy helpers, and workflow prompts.
- Site profiles are private runtime configuration, not framework code.

## Request Pattern

1. User sends a LINE message.
2. Hermes starts or resumes the conversation session.
3. The relevant skill asks for a draft plan when a write operation is requested.
4. WordPress MCP tools create drafts or previews.
5. Public changes require approval before publish/schedule/delete/homepage/SEO-setting updates.
6. The final result is sent back by LINE reply token or push message.

## Long Tasks

LINE reply tokens are short-lived and single-use. Long-running SEO or media generation jobs should:

- Acknowledge the request immediately.
- Continue in a background Hermes task or scheduler.
- Send progress only at useful milestones.
- Use push messages or a fresh postback token for completion and approval.

