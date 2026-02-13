from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{uuid4().hex[:8]}"


def default_run_dir() -> Path:
    return Path("runs") / new_run_id()
