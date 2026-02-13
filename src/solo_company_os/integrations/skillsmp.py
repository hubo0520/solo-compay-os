from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class SkillsMPConfig:
    api_key: str
    base_url: str = "https://skillsmp.com"


class SkillsMPClient:
    def __init__(self, config: SkillsMPConfig):
        self.config = config

    @classmethod
    def from_env(cls) -> "SkillsMPClient":
        api_key = os.environ.get("SKILLSMP_API_KEY")
        if not api_key:
            raise RuntimeError("Missing SKILLSMP_API_KEY. Get one from https://skillsmp.com/docs/api")
        base_url = os.environ.get("SKILLSMP_BASE_URL", "https://skillsmp.com")
        return cls(SkillsMPConfig(api_key=api_key, base_url=base_url))

    def keyword_search(self, q: str, *, page: int = 1, limit: int = 10, sort_by: str = "stars") -> Dict[str, Any]:
        url = self.config.base_url.rstrip("/") + "/api/v1/skills/search"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        params = {"q": q, "page": page, "limit": limit, "sortBy": sort_by}
        with httpx.Client(timeout=30) as client:
            r = client.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json()

    def ai_search(self, q: str) -> Dict[str, Any]:
        url = self.config.base_url.rstrip("/") + "/api/v1/skills/ai-search"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        params = {"q": q}
        with httpx.Client(timeout=60) as client:
            r = client.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json()
