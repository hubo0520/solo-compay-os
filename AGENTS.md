# AGENTS.md

This file is written for **AI coding agents** (and humans) contributing to this repository.

> Goal: keep this repo a **teaching-quality** reference implementation of an "agent one-person company" that is **runnable**, **readable**, and **easy to extend**.

## Core principles

1. **Runnable first**
   - `solo-company run "..." --provider mock` must always work without any keys.
   - CI should run end-to-end using `MockProvider`.

2. **Progressive disclosure**
   - Skills are discovered by metadata first (frontmatter), then instructions, then resources.
   - Do not load all skill bodies into context unless necessary.

3. **Structured outputs**
   - Any LLM-produced artifact must be parsed into a strict schema (JSON).
   - If parsing fails, record a warning in the trace instead of crashing.

4. **Trace everything**
   - Every significant step emits a JSONL trace event.
   - Runs are replayable: `runs/<id>/plan.json` + `trace.jsonl` + generated workspace.

5. **Small, boring tech**
   - Prefer standard library + a few well-known libs (Typer, Pydantic, PyYAML, Rich).
   - Avoid "framework soup" in v0.1.

## Repo layout

- `src/solo_company_os/cli.py`  
  Typer CLI entrypoint (`solo-company`).

- `src/solo_company_os/core/skill.py`  
  Parses SKILL.md (YAML frontmatter + Markdown body).

- `src/solo_company_os/core/skill_index.py`  
  Discovers skills under:
  - `.agents/skills/`
  - `.github/skills/`
  - `.claude/skills/`
  - `~/.claude/skills/`, `~/.codex/skills/`

- `src/solo_company_os/core/orchestrator.py`  
  Plan → execute work orders → write artifacts → RUN.md

- `src/solo_company_os/core/providers/`  
  Provider abstraction:
  - `mock.py`: deterministic, offline, used by CI
  - `openai_compatible.py`: OpenAI-compatible `/v1/chat/completions` for real runs

- `.agents/skills/*/SKILL.md`  
  Example skills shipped with the repo.

- `scenarios/`  
  Example mission files.

## Output contract conventions

For **all skills** in this repo, the active agent must return **ONLY JSON**:

```json
{
  "files": [{"path": "...", "content": "..."}],
  "summary": "short summary",
  "warnings": ["optional"]
}
```

- Paths are **relative to workspace root**.
- The orchestrator writes files to disk and records them in trace.

## Style & quality

- Python: target 3.10+, type hints required for new code.
- Keep functions small and testable.
- Add unit tests for bugfixes and new behaviors.

## Roadmap tasks (safe to implement)

If you are an AI agent asked to extend the project, prioritize:

1. Add `solo-company eval` to run scenario missions and assert expected files exist.
2. Add a "replay" command to render a run from `trace.jsonl`.
3. Add a safer sandbox for script execution (skills may ship scripts).
4. Add optional Git integration (create a repo, commit, branch, diff).

## What NOT to do (for now)

- Don't add heavy web UIs until core pipeline is stable.
- Don't add long-running background workers.
- Don't auto-execute untrusted scripts by default.
