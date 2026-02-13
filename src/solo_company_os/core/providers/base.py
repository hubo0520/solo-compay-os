from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMMessage:
    role: str  # system|user|assistant
    content: str


class LLMProvider(ABC):
    """Minimal provider interface.

    This project purposely keeps the provider contract small:
    - provide `complete_json()` for structured outputs.
    """

    @abstractmethod
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
        raise NotImplementedError
