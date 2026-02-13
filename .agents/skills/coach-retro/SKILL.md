---
name: coach-retro
description: Write a short retrospective explaining what was built, what was learned, and next improvements. Use at the end of a run.
license: MIT
metadata:
  author: solo-company-os
  version: "0.1.0"
---

# coach-retro

## Purpose
Make the run educational: turn outputs into learning notes.

## Output contract (STRICT)
Return **ONLY JSON**:

```json
{
  "files": [
    {"path": "docs/RETRO.md", "content": "..."}
  ],
  "summary": "1-3 sentences",
  "warnings": ["optional"]
}
```

## Retro requirements
`docs/RETRO.md` should include:
- What we practiced (skills, orchestration, tools)
- What went well
- What was hard / unstable
- Concrete next steps (actionable)
