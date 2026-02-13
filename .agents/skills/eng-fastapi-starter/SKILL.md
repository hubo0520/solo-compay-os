---
name: eng-fastapi-starter
description: Scaffold a minimal FastAPI app as a runnable demo (health endpoint, simple homepage). Use when mission requires code output or a web/API demo.
license: MIT
metadata:
  author: solo-company-os
  version: "0.1.0"
compatibility: Requires Python 3.10+, install deps via pip, no database by default.
---

# eng-fastapi-starter

## Purpose
Create a minimal runnable web/API project in the workspace.

## Output contract (STRICT)
Return **ONLY JSON**:

```json
{
  "files": [
    {"path": "requirements.txt", "content": "..."},
    {"path": "app/main.py", "content": "..."},
    {"path": "README.md", "content": "..."}
  ],
  "summary": "1-3 sentences",
  "warnings": ["optional"]
}
```

## Requirements
- Use FastAPI + uvicorn
- Provide endpoints:
  - GET / -> returns either HTML or JSON (ok + short message)
  - GET /healthz -> returns {"status":"ok"}
- Include `requirements.txt` with pinned-ish ranges (>=)
- Include a generated README with run steps

## Notes
- Keep everything small and readable.
- Do not invent complex infra (DB, auth) unless explicitly requested.
