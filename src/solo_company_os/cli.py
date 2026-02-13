from __future__ import annotations

import json
import os
import yaml
from pathlib import Path
from typing import List, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core.orchestrator import run_mission
from .core.providers.mock import MockProvider
from .core.providers.openai_compatible import OpenAICompatibleProvider
from .core.skill_index import DEFAULT_SKILL_DIRS, SkillIndex, discover_skills, validate_skills
from .core.utils import default_run_dir
from .integrations.skillsmp import SkillsMPClient

app = typer.Typer(
    add_completion=False,
    help="Solo Company OS — a runnable learning project: deploy a one-person agent company powered by Agent Skills (SKILL.md).",
)

skills_app = typer.Typer(help="Manage local Agent Skills (SKILL.md folders).")
app.add_typer(skills_app, name="skills")

skillsmp_app = typer.Typer(help="Search SkillsMP marketplace (optional API key).")
app.add_typer(skillsmp_app, name="skillsmp")

console = Console()


def _load_env() -> None:
    # Load .env if present (no error if missing)
    load_dotenv(dotenv_path=Path(".env"), override=False)


def _resolve_mission_arg(mission: str) -> str:
    """Allow passing a file path as the mission argument.

    - If `mission` points to an existing file:
      - .yml/.yaml: expects a top-level `mission` string field
      - otherwise: uses whole file as mission text
    - Otherwise: treat `mission` as the mission text itself.
    """
    p = Path(mission)
    if p.exists() and p.is_file():
        if p.suffix.lower() in {".yml", ".yaml"}:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            m = data.get("mission")
            if not isinstance(m, str) or not m.strip():
                raise typer.BadParameter(f"Mission file {p} must contain a non-empty 'mission' field")
            return m.strip()
        return p.read_text(encoding="utf-8").strip()
    return mission.strip()


@app.command()
def run(
    mission: str = typer.Argument(..., help="The mission / goal statement."),
    provider: str = typer.Option(
        "mock",
        "--provider",
        "-p",
        help="LLM provider: mock | openai (openai-compatible chat completions).",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="Model name (for provider=openai). If omitted, uses OPENAI_MODEL / SCOS_MODEL.",
    ),
    skill_dir: List[str] = typer.Option(
        [],
        "--skill-dir",
        help="Additional skill root directories to scan (can repeat).",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        help="Run directory (default: runs/<run_id>).",
    ),
) -> None:
    """Run a mission and generate artifacts into a per-run workspace."""
    _load_env()
    mission = _resolve_mission_arg(mission)

    roots = list(DEFAULT_SKILL_DIRS) + skill_dir
    report = discover_skills(roots=roots, console=console)
    idx = SkillIndex(report.skills)

    if report.errors:
        console.print(Panel.fit(
            "\n".join(["Skill parse/validation errors:"] + [f"- {e}" for e in report.errors]),
            title="Warnings",
            border_style="yellow",
        ))

    if not idx.skills:
        console.print(Panel.fit(
            "No skills found. Add skills under .agents/skills/<name>/SKILL.md or pass --skill-dir.",
            title="Error",
            border_style="red",
        ))
        raise typer.Exit(code=2)

    if provider == "mock":
        prov = MockProvider()
    elif provider == "openai":
        prov = OpenAICompatibleProvider.from_env(model=model)
    else:
        raise typer.BadParameter("provider must be one of: mock, openai")

    run_dir = out or default_run_dir()
    workspace = run_dir / "workspace"

    console.print(Panel.fit(
        f"Mission: {mission}\nProvider: {provider}\nSkills loaded: {len(idx.skills)}\nRun dir: {run_dir}",
        title="Solo Company OS",
    ))

    run_mission(
        mission=mission,
        skill_index=idx,
        provider=prov,
        run_dir=run_dir,
        workspace=workspace,
        console=console,
    )


@skills_app.command("list")
def skills_list(
    skill_dir: List[str] = typer.Option(
        [],
        "--skill-dir",
        help="Additional skill root directories to scan (can repeat).",
    )
) -> None:
    """List discovered skills (name + description)."""
    roots = list(DEFAULT_SKILL_DIRS) + skill_dir
    report = discover_skills(roots=roots, console=console)
    table = Table(title=f"Discovered Skills ({len(report.skills)})")
    table.add_column("name")
    table.add_column("description")
    for s in sorted(report.skills, key=lambda x: x.frontmatter.name):
        table.add_row(s.frontmatter.name, s.frontmatter.description)
    console.print(table)
    if report.errors:
        console.print(Panel.fit(
            "\n".join(["Errors:"] + [f"- {e}" for e in report.errors]),
            title="Validation Issues",
            border_style="yellow",
        ))


@skills_app.command("validate")
def skills_validate(
    skill_dir: List[str] = typer.Option(
        [],
        "--skill-dir",
        help="Additional skill root directories to scan (can repeat).",
    )
) -> None:
    """Validate skills against the basic Agent Skills spec (frontmatter + naming)."""
    roots = list(DEFAULT_SKILL_DIRS) + skill_dir
    report = validate_skills(roots=roots)
    if report.errors:
        console.print(Panel.fit(
            "\n".join([f"Found {len(report.errors)} issue(s):"] + [f"- {e}" for e in report.errors]),
            title="Skill Validation Failed",
            border_style="red",
        ))
        raise typer.Exit(code=1)
    console.print(Panel.fit(
        f"OK. Valid skills: {len(report.skills)}\nRoots scanned: {', '.join(map(str, report.roots_scanned))}",
        title="Skill Validation Passed",
        border_style="green",
    ))


@skills_app.command("show")
def skills_show(
    name: str = typer.Argument(..., help="Skill name (folder name)."),
    skill_dir: List[str] = typer.Option([], "--skill-dir", help="Additional skill roots (repeatable)."),
    head: int = typer.Option(80, "--head", help="Print first N lines of SKILL.md body."),
) -> None:
    """Show one skill's frontmatter + body preview."""
    roots = list(DEFAULT_SKILL_DIRS) + skill_dir
    report = discover_skills(roots=roots, console=console)
    idx = SkillIndex(report.skills)
    s = idx.get(name)
    if not s:
        console.print(f"Skill not found: {name}")
        raise typer.Exit(code=2)

    body = idx.load_body(name)
    body_lines = body.splitlines()[:head]
    console.print(Panel.fit(json.dumps(s.frontmatter.model_dump(), ensure_ascii=False, indent=2), title="frontmatter"))
    console.print(Panel.fit("\n".join(body_lines), title="body (preview)"))


@skillsmp_app.command("search")
def skillsmp_search(
    query: str = typer.Argument(..., help="Search query."),
    ai: bool = typer.Option(False, "--ai", help="Use AI semantic search endpoint."),
    limit: int = typer.Option(10, "--limit", help="Max results (keyword search only)."),
    sort_by: str = typer.Option("stars", "--sort-by", help="stars|recent (keyword search only)."),
) -> None:
    """Search SkillsMP marketplace.

    Requires SKILLSMP_API_KEY env var. See https://skillsmp.com/docs/api
    """
    _load_env()
    try:
        client = SkillsMPClient.from_env()
    except Exception as e:
        console.print(Panel.fit(
            f"{e}\n\nTip: You can still browse in the website: https://skillsmp.com/search",
            title="Missing SkillsMP API Key",
            border_style="yellow",
        ))
        raise typer.Exit(code=2)

    if ai:
        data = client.ai_search(query)
    else:
        data = client.keyword_search(query, limit=limit, sort_by=sort_by)

    # Unknown schema: we print a compact view if possible, else raw JSON.
    table = Table(title="SkillsMP results")
    table.add_column("field")
    table.add_column("value")
    table.add_row("query", query)
    table.add_row("mode", "ai" if ai else "keyword")
    console.print(table)

    console.print(Panel.fit(json.dumps(data, ensure_ascii=False, indent=2)[:4000], title="response (truncated)"))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
