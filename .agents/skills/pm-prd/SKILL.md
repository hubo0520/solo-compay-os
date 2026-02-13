---
name: pm-prd
description: Write a concise PRD (overview, goals, non-goals, user stories, acceptance criteria, milestones, risks). Use when user asks for PRD/requirements/spec/MVP scope.
license: MIT
metadata:
  author: solo-company-os
  version: "0.1.0"
---

# pm-prd

## Purpose
Turn a fuzzy idea into a concrete, testable PRD.

## Use when
- The user asks for: PRD / requirements / spec / MVP / user stories / acceptance criteria
- The mission is ambiguous and needs scope control

## Do NOT use when
- The user only wants marketing copy
- The task is purely coding without product decisions

## Output contract (STRICT)
Return **ONLY JSON**:

```json
{
  "files": [
    {"path": "docs/PRD.md", "content": "..."}
  ],
  "summary": "1-3 sentences",
  "warnings": ["optional"]
}
```

## PRD structure
The generated `docs/PRD.md` must contain exactly these sections:

1. Overview
2. Goals
3. Non-goals
4. Target users & primary use cases
5. User stories
6. Acceptance criteria
7. Milestones
8. Risks & open questions

## Quality bar
- Acceptance criteria must be testable.
- Non-goals must explicitly exclude tempting scope creep.
- If mission lacks info, add open questions in the last section instead of asking the user multiple follow-ups.
