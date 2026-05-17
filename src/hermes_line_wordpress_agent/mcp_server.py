from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .approval import requires_approval
from .config import load_yaml
from .wp_client import WordPressClient

load_dotenv()

mcp = FastMCP("wordpress")


def _client() -> WordPressClient:
    return WordPressClient.from_env()


def _policy() -> dict[str, Any]:
    return load_yaml(os.getenv("POLICY_PATH", "config/policy.example.yaml"))


def _approval_guard(tool_name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    decision = requires_approval(tool_name, payload, _policy())
    if decision.required:
        return {
            "approval_required": True,
            "reason": decision.reason,
            "tool": tool_name,
            "payload": payload,
            "next_step": "Ask the LINE user to approve before calling this tool with the same payload.",
        }
    return None


@mcp.tool()
def wp_health() -> dict[str, Any]:
    """Check WordPress credentials and current API user."""
    with _client() as client:
        return client.health()


@mcp.tool()
def wp_get_post(post_id: int, post_type: str = "posts") -> dict[str, Any]:
    """Get a WordPress post/page/custom-post by ID."""
    client = _client()
    try:
        return client.get_post(post_id=post_id, post_type=post_type)
    finally:
        client.close()


@mcp.tool()
def wp_search_posts(
    query: str,
    post_type: str = "posts",
    status: str = "any",
    per_page: int = 10,
) -> list[dict[str, Any]]:
    """Search WordPress content."""
    client = _client()
    try:
        return client.search_posts(query=query, post_type=post_type, status=status, per_page=per_page)
    finally:
        client.close()


@mcp.tool()
def wp_create_post(
    title: str,
    content: str,
    status: str = "draft",
    post_type: str = "posts",
    excerpt: str | None = None,
    slug: str | None = None,
    categories: list[int] | None = None,
    tags: list[int] | None = None,
    featured_media: int | None = None,
    approved: bool = False,
) -> dict[str, Any]:
    """Create a WordPress post. Defaults to draft; publishing requires approval."""
    payload = {
        "title": title,
        "status": status,
        "post_type": post_type,
        "slug": slug,
        "categories": categories,
        "tags": tags,
        "featured_media": featured_media,
    }
    if not approved:
        blocked = _approval_guard("wp_create_post", payload)
        if blocked:
            return blocked

    client = _client()
    try:
        return client.create_post(
            title=title,
            content=content,
            status=status,
            post_type=post_type,
            excerpt=excerpt,
            slug=slug,
            categories=categories,
            tags=tags,
            featured_media=featured_media,
        )
    finally:
        client.close()


@mcp.tool()
def wp_update_post(
    post_id: int,
    post_type: str = "posts",
    title: str | None = None,
    content: str | None = None,
    excerpt: str | None = None,
    status: str | None = None,
    slug: str | None = None,
    approved: bool = False,
) -> dict[str, Any]:
    """Update a WordPress post/page/custom-post."""
    payload = {"post_id": post_id, "post_type": post_type, "status": status}
    if not approved:
        blocked = _approval_guard("wp_update_post", payload)
        if blocked:
            return blocked

    client = _client()
    try:
        return client.update_post(
            post_id=post_id,
            post_type=post_type,
            title=title,
            content=content,
            excerpt=excerpt,
            status=status,
            slug=slug,
        )
    finally:
        client.close()


@mcp.tool()
def wp_schedule_post(
    post_id: int,
    date_gmt: str,
    post_type: str = "posts",
    approved: bool = False,
) -> dict[str, Any]:
    """Schedule a post by setting status=future and date_gmt."""
    payload = {"post_id": post_id, "post_type": post_type, "status": "future", "date_gmt": date_gmt}
    if not approved:
        blocked = _approval_guard("wp_schedule_post", payload)
        if blocked:
            return blocked

    client = _client()
    try:
        return client.schedule_post(post_id=post_id, date_gmt=date_gmt, post_type=post_type)
    finally:
        client.close()


@mcp.tool()
def wp_upload_media(
    file_path: str,
    title: str | None = None,
    alt_text: str | None = None,
    caption: str | None = None,
) -> dict[str, Any]:
    """Upload a local file to WordPress Media Library."""
    client = _client()
    try:
        return client.upload_media(file_path=file_path, title=title, alt_text=alt_text, caption=caption)
    finally:
        client.close()


@mcp.tool()
def wp_set_featured_image(post_id: int, media_id: int, post_type: str = "posts") -> dict[str, Any]:
    """Set featured image for a post."""
    client = _client()
    try:
        return client.set_featured_image(post_id=post_id, media_id=media_id, post_type=post_type)
    finally:
        client.close()


@mcp.tool()
def wp_get_preview_url(post_id: int, post_type: str = "posts") -> str:
    """Get a preview or public URL for a post."""
    client = _client()
    try:
        return client.get_preview_url(post_id=post_id, post_type=post_type)
    finally:
        client.close()


@mcp.tool()
def wp_set_seo_meta(
    post_id: int,
    title: str | None = None,
    description: str | None = None,
    focus_keyword: str | None = None,
    plugin: str = "auto",
    approved: bool = False,
) -> dict[str, Any]:
    """Set SEO meta through the optional WordPress companion plugin."""
    payload = {
        "post_id": post_id,
        "target": "seo_settings",
        "title": title,
        "description": description,
        "focus_keyword": focus_keyword,
        "plugin": plugin,
    }
    if not approved:
        blocked = _approval_guard("wp_set_seo_meta", payload)
        if blocked:
            return blocked

    client = _client()
    try:
        return client.set_seo_meta(
            post_id=post_id,
            title=title,
            description=description,
            focus_keyword=focus_keyword,
            plugin=plugin,
        )
    finally:
        client.close()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
