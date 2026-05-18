from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import shlex
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request


LINE_REPLY_ENDPOINT = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH_ENDPOINT = "https://api.line.me/v2/bot/message/push"
LINE_LOADING_ENDPOINT = "https://api.line.me/v2/bot/chat/loading/start"
LINE_TEXT_LIMIT = 5000
LINE_LOADING_SECONDS = {5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60}


def _csv(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class GatewaySettings:
    line_channel_secret: str
    line_channel_access_token: str
    allowed_user_ids: set[str]
    allowed_group_ids: set[str]
    allowed_room_ids: set[str]
    require_allowlist: bool
    reply_mode: str
    ack_message: str
    unauthorized_message: str
    loading_enabled: bool
    loading_seconds: int
    loading_skip_ack: bool
    hermes_bin: str
    hermes_model: str
    hermes_provider: str
    hermes_toolsets: str
    hermes_workdir: str
    hermes_timeout_seconds: float
    hermes_extra_args: list[str]
    hermes_prefix_prompt: str

    @classmethod
    def from_env(cls) -> GatewaySettings:
        secret = os.getenv("LINE_CHANNEL_SECRET", "")
        token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
        if not secret:
            raise RuntimeError("LINE_CHANNEL_SECRET is required")
        if not token:
            raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN is required")

        reply_mode = os.getenv("LINE_REPLY_MODE", "ack_then_push").strip().lower()
        if reply_mode not in {"ack_then_push", "reply"}:
            raise RuntimeError("LINE_REPLY_MODE must be ack_then_push or reply")

        timeout = float(os.getenv("HERMES_TIMEOUT_SECONDS", "300"))
        prefix = os.getenv("HERMES_PREFIX_PROMPT", DEFAULT_PREFIX_PROMPT).strip()
        loading_seconds = int(os.getenv("LINE_LOADING_SECONDS", "60"))
        if loading_seconds not in LINE_LOADING_SECONDS:
            raise RuntimeError("LINE_LOADING_SECONDS must be one of 5, 10, ..., 60")

        return cls(
            line_channel_secret=secret,
            line_channel_access_token=token,
            allowed_user_ids=_csv("LINE_ALLOWED_USER_IDS"),
            allowed_group_ids=_csv("LINE_ALLOWED_GROUP_IDS"),
            allowed_room_ids=_csv("LINE_ALLOWED_ROOM_IDS"),
            require_allowlist=_bool_env("LINE_REQUIRE_ALLOWLIST", default=False),
            reply_mode=reply_mode,
            ack_message=os.getenv("LINE_ACK_MESSAGE", "Received. Hermes is working on it."),
            unauthorized_message=os.getenv(
                "LINE_UNAUTHORIZED_MESSAGE",
                "This LINE account is not authorized.",
            ),
            loading_enabled=_bool_env("LINE_LOADING_ENABLED", default=True),
            loading_seconds=loading_seconds,
            loading_skip_ack=_bool_env("LINE_LOADING_SKIP_ACK", default=True),
            hermes_bin=os.getenv("HERMES_BIN", "hermes"),
            hermes_model=os.getenv("HERMES_MODEL", ""),
            hermes_provider=os.getenv("HERMES_PROVIDER", ""),
            hermes_toolsets=os.getenv("HERMES_TOOLSETS", "wordpress"),
            hermes_workdir=os.getenv("HERMES_WORKDIR", "."),
            hermes_timeout_seconds=timeout,
            hermes_extra_args=shlex.split(os.getenv("HERMES_EXTRA_ARGS", "")),
            hermes_prefix_prompt=prefix,
        )


DEFAULT_PREFIX_PROMPT = """You are Hermes Agent operating a WordPress site from LINE.
Use the wordpress MCP tools when site changes are needed. Default to draft content.
Do not publish, schedule, delete, or change protected SEO/homepage settings until the
LINE user has explicitly approved the exact action. Keep the final LINE response concise
and include relevant post IDs, status values, and preview/public URLs."""


class EventDeduper:
    def __init__(self, max_items: int = 2048) -> None:
        self._max_items = max_items
        self._seen: OrderedDict[str, None] = OrderedDict()

    def first_seen(self, event_id: str | None) -> bool:
        if not event_id:
            return True
        if event_id in self._seen:
            self._seen.move_to_end(event_id)
            return False
        self._seen[event_id] = None
        while len(self._seen) > self._max_items:
            self._seen.popitem(last=False)
        return True


deduper = EventDeduper()
app = FastAPI(title="Hermes LINE WordPress Gateway")


def verify_line_signature(channel_secret: str, body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    digest = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, signature)


def source_target(source: dict[str, Any]) -> str | None:
    source_type = source.get("type")
    if source_type == "group":
        return source.get("groupId")
    if source_type == "room":
        return source.get("roomId")
    return source.get("userId")


def source_summary(source: dict[str, Any]) -> str:
    parts = [f"type={source.get('type', 'unknown')}"]
    for key in ("userId", "groupId", "roomId"):
        if source.get(key):
            parts.append(f"{key}={source[key]}")
    return " ".join(parts)


def is_authorized(settings: GatewaySettings, source: dict[str, Any]) -> bool:
    user_id = source.get("userId")
    group_id = source.get("groupId")
    room_id = source.get("roomId")
    has_allowlist = bool(
        settings.allowed_user_ids or settings.allowed_group_ids or settings.allowed_room_ids
    )
    if not has_allowlist and not settings.require_allowlist:
        return True
    return (
        bool(user_id and user_id in settings.allowed_user_ids)
        or bool(group_id and group_id in settings.allowed_group_ids)
        or bool(room_id and room_id in settings.allowed_room_ids)
    )


def build_prompt(settings: GatewaySettings, text: str, source: dict[str, Any]) -> str:
    return (
        f"{settings.hermes_prefix_prompt}\n\n"
        f"LINE source: {source_summary(source)}\n\n"
        "User message:\n"
        f"{text.strip()}"
    )


def text_messages(text: str, limit: int = LINE_TEXT_LIMIT) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    remaining = text.strip() or "(empty response)"
    while remaining and len(chunks) < 5:
        chunk = remaining[:limit]
        chunks.append({"type": "text", "text": chunk})
        remaining = remaining[limit:]
    if remaining and chunks:
        chunks[-1]["text"] = chunks[-1]["text"][: limit - 30] + "\n\n[truncated]"
    return chunks


async def line_post(settings: GatewaySettings, endpoint: str, payload: dict[str, Any]) -> None:
    headers = {
        "Authorization": f"Bearer {settings.line_channel_access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()


async def reply_text(settings: GatewaySettings, reply_token: str, text: str) -> None:
    await line_post(
        settings,
        LINE_REPLY_ENDPOINT,
        {"replyToken": reply_token, "messages": text_messages(text)},
    )


async def push_text(settings: GatewaySettings, to: str, text: str) -> None:
    await line_post(settings, LINE_PUSH_ENDPOINT, {"to": to, "messages": text_messages(text)})


async def start_loading(settings: GatewaySettings, source: dict[str, Any]) -> bool:
    if not settings.loading_enabled or source.get("type") != "user":
        return False
    user_id = source.get("userId")
    if not user_id:
        return False
    try:
        await line_post(
            settings,
            LINE_LOADING_ENDPOINT,
            {"chatId": user_id, "loadingSeconds": settings.loading_seconds},
        )
    except httpx.HTTPError:
        return False
    return True


async def run_hermes(settings: GatewaySettings, text: str, source: dict[str, Any]) -> str:
    prompt = build_prompt(settings, text, source)
    argv = [settings.hermes_bin, "-z", prompt]
    if settings.hermes_model:
        argv.extend(["--model", settings.hermes_model])
    if settings.hermes_provider:
        argv.extend(["--provider", settings.hermes_provider])
    if settings.hermes_toolsets:
        argv.extend(["--toolsets", settings.hermes_toolsets])
    argv.extend(settings.hermes_extra_args)

    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=settings.hermes_workdir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return f"Hermes binary not found: {settings.hermes_bin}"

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=settings.hermes_timeout_seconds,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return "Hermes timed out before finishing the task."

    out = stdout.decode("utf-8", errors="replace").strip()
    err = stderr.decode("utf-8", errors="replace").strip()
    if proc.returncode != 0:
        detail = err or out or f"Hermes exited with code {proc.returncode}."
        return f"Hermes failed:\n{detail}"
    return out or "(Hermes returned no text.)"


async def process_event(settings: GatewaySettings, event: dict[str, Any]) -> None:
    source = event.get("source") or {}
    target = source_target(source)
    if not target:
        return
    text = ((event.get("message") or {}).get("text") or "").strip()
    if not text:
        await push_text(settings, target, "Only text messages are supported for now.")
        return
    result = await run_hermes(settings, text, source)
    await push_text(settings, target, result)


@app.get("/healthz")
async def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.post("/line/webhook")
async def line_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str | None = Header(default=None),
) -> dict[str, bool]:
    settings = GatewaySettings.from_env()
    body = await request.body()
    if not verify_line_signature(settings.line_channel_secret, body, x_line_signature):
        raise HTTPException(status_code=401, detail="invalid LINE signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON") from exc

    for event in payload.get("events", []):
        event_id = event.get("webhookEventId")
        if not deduper.first_seen(event_id):
            continue
        if event.get("type") != "message":
            continue
        message = event.get("message") or {}
        if message.get("type") != "text":
            continue

        reply_token = event.get("replyToken")
        source = event.get("source") or {}
        text = (message.get("text") or "").strip()

        if text == "/whoami" and reply_token:
            await reply_text(settings, reply_token, source_summary(source))
            continue

        if not is_authorized(settings, source):
            if reply_token:
                await reply_text(settings, reply_token, settings.unauthorized_message)
            continue

        if settings.reply_mode == "reply":
            if reply_token:
                await start_loading(settings, source)
                result = await run_hermes(settings, text, source)
                await reply_text(settings, reply_token, result)
            continue

        loading_started = await start_loading(settings, source)
        if reply_token and not (loading_started and settings.loading_skip_ack):
            await reply_text(settings, reply_token, settings.ack_message)
        background_tasks.add_task(process_event, settings, event)

    return {"ok": True}


def main() -> None:
    import uvicorn

    host = os.getenv("LINE_GATEWAY_HOST", "127.0.0.1")
    port = int(os.getenv("LINE_GATEWAY_PORT", "8787"))
    uvicorn.run("hermes_line_wordpress_agent.line_gateway:app", host=host, port=port)


if __name__ == "__main__":
    main()
