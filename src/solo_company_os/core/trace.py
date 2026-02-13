from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TraceEvent:
    ts: str
    type: str
    payload: Dict[str, Any]


class TraceRecorder:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        evt = TraceEvent(ts=utc_now_iso(), type=type, payload=payload or {})
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt.__dict__, ensure_ascii=False) + "\n")
