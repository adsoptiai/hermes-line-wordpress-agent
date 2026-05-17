from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


def load_yaml(path: str | os.PathLike[str]) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    with file_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return _expand_env(data)


class SiteProfile(BaseModel):
    slug: str = "default"
    name: str = "Default Site"
    public_url: str = ""
    wordpress_base_url: str = ""
    timezone: str = "UTC"


class ApprovalConfig(BaseModel):
    require_for: list[str] = Field(default_factory=list)


class LoadedConfig(BaseModel):
    site: SiteProfile = Field(default_factory=SiteProfile)
    approval: ApprovalConfig = Field(default_factory=ApprovalConfig)
    raw: dict[str, Any] = Field(default_factory=dict)


def load_site_profile(path: str | None = None) -> LoadedConfig:
    profile_path = path or os.getenv("SITE_PROFILE_PATH", "config/site.profile.example.yaml")
    raw = load_yaml(profile_path)
    return LoadedConfig(
        site=SiteProfile(**raw.get("site", {})),
        approval=ApprovalConfig(**raw.get("approval", {})),
        raw=raw,
    )

