---
name: skill-template
description: A template skill you can copy to create your own SKILL.md quickly. Use when authoring new skills.
license: MIT
metadata:
  author: solo-company-os
  version: "0.1.0"
---

# skill-template

## How to use
1) Copy this folder:
- `.agents/skills/skill-template/` -> `.agents/skills/<your-skill-name>/`
2) Rename the `name:` field to match the folder name.
3) Rewrite `description:` so the model can pick it automatically.
4) Write clear "Use when" / "Do NOT use when" criteria.
5) Define an output contract (JSON) so downstream tools can parse it.

## Skeleton

### Purpose
What this skill is for.

### Use when
- Bullet list of triggers.

### Do NOT use when
- Bullet list of out-of-scope cases.

### Output contract (STRICT)
Return ONLY JSON:
- files: list of {path, content}
- summary: short summary
- warnings: list of strings

### Procedure
1) Step-by-step workflow.
2) Include examples.
