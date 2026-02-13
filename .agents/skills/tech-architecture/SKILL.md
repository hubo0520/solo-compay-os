---
name: tech-architecture
description: Propose a practical architecture and repo structure for the mission. Include module boundaries, tradeoffs, and a minimal tech stack. Use when starting implementation.
license: MIT
metadata:
  author: solo-company-os
  version: "0.1.0"
---

# tech-architecture

## Purpose
Translate product intent into an implementable technical plan.

## Output contract (STRICT)
Return **ONLY JSON**:

```json
{
  "files": [
    {"path": "docs/ARCHITECTURE.md", "content": "..."}
  ],
  "summary": "1-3 sentences",
  "warnings": ["optional"]
}
```

## Architecture doc requirements
`docs/ARCHITECTURE.md` must include:
- Overview (what we're building)
- High-level components diagram (ASCII is fine)
- Data flow (mission -> plan -> work orders -> artifacts)
- Key decisions + tradeoffs
- Minimal repo structure
- Testing strategy
- Known risks

## Constraints
- Keep it minimal and runnable.
- Prefer boring, well-known tools.
