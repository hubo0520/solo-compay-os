---
name: pm-backlog
description: Convert a PRD into a prioritized backlog (P0/P1/P2), with clear deliverables and dependencies. Use after a PRD exists.
license: MIT
metadata:
  author: solo-company-os
  version: "0.1.0"
---

# pm-backlog

## Purpose
Turn PRD into an executable backlog.

## Input assumptions
- There is a PRD or at least a mission statement.
- You may infer a minimal PRD from mission if PRD is missing, but note assumptions.

## Output contract (STRICT)
Return **ONLY JSON**:

```json
{
  "files": [
    {"path": "docs/BACKLOG.md", "content": "..."}
  ],
  "summary": "1-3 sentences",
  "warnings": ["optional"]
}
```

## Backlog format
`docs/BACKLOG.md` should include:
- a short summary of scope
- a table with columns: Priority, Work Item, Definition of Done, Dependencies
- 8-20 items total, focused on MVP
