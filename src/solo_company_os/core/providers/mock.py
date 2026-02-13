from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from .base import LLMProvider


def _stable_id(text: str, n: int = 6) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return h[:n]


class MockProvider(LLMProvider):
    """A deterministic, offline provider.

    It does NOT attempt to be intelligent. It exists so:
    - the repo is runnable without any API keys
    - CI can run end-to-end
    """

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
        timeout_s: int = 120,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if "Plan" in schema_hint:
            return self._plan(user)
        if "SkillExecutionResult" in schema_hint:
            return self._execute(user)
        # fallback
        return {"ok": True, "note": "mock provider fallback", "schema_hint": schema_hint}

    def _extract_mission(self, user: str) -> str:
        m = re.search(r"MISSION:\s*(.+)", user)
        if m:
            return m.group(1).strip()
        # fallback: use first line
        return user.strip().splitlines()[0][:200]

    def _plan(self, user: str) -> Dict[str, Any]:
        mission = self._extract_mission(user)
        # Very naive heuristics to pick build vs learn
        mode = "build" if any(k in mission.lower() for k in ["build", "生成", "项目", "代码", "landing", "api"]) else "learn"

        work_orders = [
            {
                "id": "WO-1",
                "title": "Write a concise PRD with acceptance criteria",
                "skill": "pm-prd",
                "outputs": [{"path": "docs/PRD.md", "purpose": "product requirements"}],
            },
            {
                "id": "WO-2",
                "title": "Turn PRD into a prioritized backlog",
                "skill": "pm-backlog",
                "outputs": [{"path": "docs/BACKLOG.md", "purpose": "work breakdown"}],
            },
            {
                "id": "WO-3",
                "title": "Propose architecture and repo structure",
                "skill": "tech-architecture",
                "outputs": [{"path": "docs/ARCHITECTURE.md", "purpose": "tech design"}],
            },
        ]

        if mode == "build":
            work_orders += [
                {
                    "id": "WO-4",
                    "title": "Implement a minimal FastAPI app (demo product output)",
                    "skill": "eng-fastapi-starter",
                    "outputs": [
                        {"path": "app/main.py", "purpose": "FastAPI app"},
                        {"path": "requirements.txt", "purpose": "runtime deps"},
                    ],
                },
                {
                    "id": "WO-5",
                    "title": "Add pytest tests and basic quality checks",
                    "skill": "qa-pytest",
                    "outputs": [
                        {"path": "tests/test_app.py", "purpose": "smoke test"},
                        {"path": "pyproject.toml", "purpose": "tooling config"},
                    ],
                },
            ]

        work_orders.append(
            {
                "id": "WO-6",
                "title": "Write a short retrospective and next steps",
                "skill": "coach-retro",
                "outputs": [{"path": "docs/RETRO.md", "purpose": "learning notes"}],
            }
        )

        return {
            "mode": mode,
            "work_orders": work_orders,
            "assumptions": [
                "This is a learning project; mock outputs are deterministic placeholders.",
                "Replace the provider with a real LLM for higher-quality artifacts.",
            ],
        }

    def _execute(self, user: str) -> Dict[str, Any]:
        # Try to detect skill name
        skill = "unknown-skill"
        m = re.search(r"SKILL:\s*([a-z0-9-]+)", user)
        if m:
            skill = m.group(1)

        mission = self._extract_mission(user)
        rid = _stable_id(skill + "::" + mission)

        # per-skill deterministic outputs
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        files = []
        if skill == "pm-prd":
            files.append(
                {
                    "path": "docs/PRD.md",
                    "content": f"""# PRD (Mock)\n\nGenerated: {now}\n\n## Overview\nMission: {mission}\n\n## Goals\n- Deliver a runnable demo that teaches agent/skills basics\n\n## Non-goals\n- Real-world legal incorporation\n\n## Target users & primary use cases\n- Learners who want to understand agent orchestration\n- Developers who want a reference repo structure\n\n## User stories\n- As a user, I can run a mission and get artifacts generated into a workspace.\n- As a user, I can list and inspect skills discovered from disk.\n\n## Acceptance criteria\n- `solo-company run` produces a `runs/<id>/workspace` folder with docs and (optionally) code.\n\n## Milestones\n- v0.1: CLI + skill discovery + mock provider\n\n## Risks & open questions\n- How to sandbox script execution safely?\n""" 
                }
            )
        elif skill == "pm-backlog":
            files.append(
                {
                    "path": "docs/BACKLOG.md",
                    "content": f"""# Backlog (Mock)\n\nRun: {rid}\n\n| Priority | Item | Done |\n|---|---|---|\n| P0 | Skill discovery & validation | ☐ |\n| P0 | Orchestrator run pipeline | ☐ |\n| P1 | SkillsMP search integration | ☐ |\n| P1 | Scenario eval harness | ☐ |\n| P2 | Web dashboard | ☐ |\n""" 
                }
            )
        elif skill == "tech-architecture":
            files.append(
                {
                    "path": "docs/ARCHITECTURE.md",
                    "content": f"""# Architecture (Mock)\n\n## Components\n- CLI (Typer)\n- SkillIndex (discovers SKILL.md)\n- Orchestrator (plan -> execute -> write artifacts)\n- Provider (mock or OpenAI-compatible)\n- Trace (JSONL events)\n\n## Data flow\nMission -> Plan -> WorkOrders -> Skill Execution -> Files -> Run Report\n\n## Notes\nThis file is generated by the mock provider. Replace with real LLM output for richer content.\n""" 
                }
            )
        elif skill == "eng-fastapi-starter":
            files.extend(
                [
                    {
                        "path": "requirements.txt",
                        "content": "fastapi>=0.110\nuvicorn>=0.29\n",
                    },
                    {
                        "path": "app/main.py",
                        "content": f"""from fastapi import FastAPI\n\napp = FastAPI(title='Demo Landing (Mock)')\n\n@app.get('/')\ndef home():\n    return {{\"ok\": True, \"mission\": {mission!r}}}\n\n@app.get('/healthz')\ndef healthz():\n    return {{\"status\": 'ok'}}\n""" 
                    },
                    {
                        "path": "README.md",
                        "content": """# Generated Demo App (Mock)\n\nRun:\n\n```bash\npip install -r requirements.txt\nuvicorn app.main:app --reload\n```\n\nOpen: http://127.0.0.1:8000\n""" 
                    },
                ]
            )
        elif skill == "qa-pytest":
            files.extend(
                [
                    {
                        "path": "pyproject.toml",
                        "content": """[tool.pytest.ini_options]\naddopts = '-q'\n""" 
                    },
                    {
                        "path": "tests/test_app.py",
                        "content": """from fastapi.testclient import TestClient\n\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_healthz():\n    r = client.get('/healthz')\n    assert r.status_code == 200\n    assert r.json()['status'] == 'ok'\n""" 
                    },
                ]
            )
        elif skill == "coach-retro":
            files.append(
                {
                    "path": "docs/RETRO.md",
                    "content": f"""# Retro (Mock)\n\n## What you practiced\n- Skill discovery (SKILL.md parsing)\n- Simple orchestration pipeline\n- Trace logging\n\n## What to improve\n- Add a real LLM provider\n- Add eval scenarios & CI\n- Add a web dashboard for trace + artifacts\n""" 
                }
            )
        else:
            files.append(
                {
                    "path": f"docs/{skill}.md",
                    "content": f"""# {skill} (Mock)\n\nMission: {mission}\n\nThis is a placeholder output from MockProvider.\n""" 
                }
            )

        return {
            "files": files,
            "summary": f"Mock execution complete for {skill}. Wrote {len(files)} file(s).",
            "warnings": [
                "MockProvider output is template-based. Use a real LLM provider for meaningful content."
            ],
        }
