from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx


class WordPressError(RuntimeError):
    """Raised when WordPress returns an unsuccessful response."""


class WordPressClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        app_password: str,
        bridge_token: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        if not base_url:
            raise ValueError("WORDPRESS_BASE_URL is required")
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/wp-json/wp/v2"
        self.bridge_base = f"{self.base_url}/wp-json/hermes-agent/v1"
        self.bridge_token = bridge_token or ""
        token = base64.b64encode(f"{username}:{app_password}".encode("utf-8")).decode("ascii")
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "Authorization": f"Basic {token}",
                "User-Agent": "hermes-line-wordpress-agent/0.1",
            },
        )

    def __enter__(self) -> "WordPressClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @classmethod
    def from_env(cls) -> "WordPressClient":
        return cls(
            base_url=os.getenv("WORDPRESS_BASE_URL", ""),
            username=os.getenv("WORDPRESS_USERNAME", ""),
            app_password=os.getenv("WORDPRESS_APP_PASSWORD", ""),
            bridge_token=os.getenv("WORDPRESS_BRIDGE_TOKEN"),
        )

    def close(self) -> None:
        self.client.close()

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        response = self.client.request(method, url, **kwargs)
        if response.status_code >= 400:
            raise WordPressError(f"{method} {url} failed: {response.status_code} {response.text}")
        if not response.content:
            return None
        return response.json()

    def _wp(self, path: str) -> str:
        return f"{self.api_base}/{path.lstrip('/')}"

    def _bridge(self, path: str) -> str:
        return f"{self.bridge_base}/{path.lstrip('/')}"

    def health(self) -> dict[str, Any]:
        result = self._request("GET", self._wp("users/me?context=edit"))
        return {
            "ok": True,
            "site": self.base_url,
            "user": {
                "id": result.get("id"),
                "name": result.get("name"),
                "slug": result.get("slug"),
            },
        }

    def get_post(self, post_id: int, post_type: str = "posts", context: str = "edit") -> dict[str, Any]:
        return self._request("GET", self._wp(f"{post_type}/{post_id}"), params={"context": context})

    def search_posts(
        self,
        query: str,
        post_type: str = "posts",
        status: str = "any",
        per_page: int = 10,
    ) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            self._wp(post_type),
            params={"search": query, "status": status, "per_page": per_page, "context": "edit"},
        )

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        post_type: str = "posts",
        excerpt: str | None = None,
        slug: str | None = None,
        categories: list[int] | None = None,
        tags: list[int] | None = None,
        featured_media: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": title,
            "content": content,
            "status": status,
        }
        if excerpt is not None:
            payload["excerpt"] = excerpt
        if slug is not None:
            payload["slug"] = slug
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags
        if featured_media:
            payload["featured_media"] = featured_media
        return self._request("POST", self._wp(post_type), json=payload)

    def update_post(
        self,
        post_id: int,
        post_type: str = "posts",
        **fields: Any,
    ) -> dict[str, Any]:
        payload = {key: value for key, value in fields.items() if value is not None}
        return self._request("POST", self._wp(f"{post_type}/{post_id}"), json=payload)

    def schedule_post(
        self,
        post_id: int,
        date_gmt: str,
        post_type: str = "posts",
    ) -> dict[str, Any]:
        return self.update_post(post_id, post_type=post_type, status="future", date_gmt=date_gmt)

    def upload_media(
        self,
        file_path: str,
        title: str | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
    ) -> dict[str, Any]:
        path = Path(file_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        headers = {
            "Content-Disposition": f'attachment; filename="{path.name}"',
            "Content-Type": mime_type,
        }
        with path.open("rb") as handle:
            media = self._request("POST", self._wp("media"), headers=headers, content=handle.read())

        update: dict[str, Any] = {}
        if title:
            update["title"] = title
        if alt_text:
            update["alt_text"] = alt_text
        if caption:
            update["caption"] = caption
        if update:
            media = self._request("POST", self._wp(f"media/{media['id']}"), json=update)
        return media

    def set_featured_image(
        self,
        post_id: int,
        media_id: int,
        post_type: str = "posts",
    ) -> dict[str, Any]:
        return self.update_post(post_id, post_type=post_type, featured_media=media_id)

    def get_preview_url(self, post_id: int, post_type: str = "posts") -> str:
        post = self.get_post(post_id, post_type=post_type, context="edit")
        return post.get("preview_link") or post.get("link") or ""

    def set_seo_meta(
        self,
        post_id: int,
        title: str | None = None,
        description: str | None = None,
        focus_keyword: str | None = None,
        plugin: str = "auto",
    ) -> dict[str, Any]:
        headers = {"X-Hermes-Bridge-Token": self.bridge_token}
        payload = {
            "title": title,
            "description": description,
            "focus_keyword": focus_keyword,
            "plugin": plugin,
        }
        return self._request(
            "POST",
            self._bridge(f"seo-meta/{post_id}"),
            headers=headers,
            json={key: value for key, value in payload.items() if value is not None},
        )
