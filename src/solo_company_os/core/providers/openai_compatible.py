from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from .base import LLMProvider


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Remove Markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", text)
        text = re.sub(r"\n```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        m = _JSON_RE.search(text)
        if not m:
            raise ValueError("Model did not return JSON")
        return json.loads(m.group(0))


@dataclass
class OpenAICompatibleConfig:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"  # placeholder default; override in env/CLI
    headers: Optional[Dict[str, str]] = None


class OpenAICompatibleProvider(LLMProvider):
    """A minimal OpenAI-compatible Chat Completions provider.

    This is intentionally minimal and works with many providers that implement the
    `/v1/chat/completions` schema (OpenAI-compatible servers, gateway proxies, etc.).

    NOTE: In real usage you may want:
    - retries with backoff
    - streaming
    - structured output features (if your provider supports them)
    """

    def __init__(self, config: OpenAICompatibleConfig):
        self.config = config

    @classmethod
    def from_env(cls, *, model: Optional[str] = None) -> "OpenAICompatibleProvider":
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("SCOS_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY (or SCOS_API_KEY) for openai provider")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = model or os.environ.get("OPENAI_MODEL") or os.environ.get("SCOS_MODEL") or "gpt-4o-mini"
        return cls(OpenAICompatibleConfig(api_key=api_key, base_url=base_url, model=model))

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
        timeout_s: int = 120,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        if self.config.headers:
            headers.update(self.config.headers)

        # We strongly nudge JSON-only output. For reliability, keep prompts short and explicit.
        system_msg = (
            system
            + "\n\n"
            + "You MUST output ONLY valid JSON. No Markdown fences, no commentary."
            + f"\nSchema hint: {schema_hint}"
        )

        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if extra:
            payload.update(extra)

        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Unexpected response schema from provider: {data}") from e

        return _extract_json(content)
