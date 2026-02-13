---
name: qa-pytest
description: Add pytest tests and minimal quality checks for a Python project (FastAPI smoke test). Use after initial code exists.
license: MIT
metadata:
  author: solo-company-os
  version: "0.1.0"
compatibility: Requires pytest; uses fastapi.testclient.
---

# qa-pytest

## Purpose
Create tests that catch regressions and prove the app runs.

## Output contract (STRICT)
Return **ONLY JSON**:

```json
{
  "files": [
    {"path": "tests/test_app.py", "content": "..."},
    {"path": "pyproject.toml", "content": "..."}
  ],
  "summary": "1-3 sentences",
  "warnings": ["optional"]
}
```

## Test requirements
- At least 1 smoke test for /healthz
- Prefer fastapi.testclient
- Keep tests deterministic and fast
