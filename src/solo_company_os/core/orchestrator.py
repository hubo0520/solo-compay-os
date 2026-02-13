from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from rich.console import Console
from rich.table import Table

from .providers.base import LLMProvider
from .schema import Plan, SkillExecutionResult
from .skill_index import SkillIndex
from .trace import TraceRecorder


@dataclass
class RunSummary:
    run_dir: Path
    workspace: Path
    plan: Plan
    written_files: List[Path]
    warnings: List[str]


PLAN_SCHEMA_HINT = "Plan(mode, work_orders[{id,title,skill,outputs[{path,purpose}]}], assumptions[])"


EXEC_SCHEMA_HINT = "SkillExecutionResult(files[{path,content}], summary, warnings[])"


def _render_skill_list(skills: Sequence[tuple[str, str]]) -> str:
    # Keep it compact for tokens.
    return "\n".join([f"- {name}: {desc}" for name, desc in skills])


def _safe_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_mission(
    *,
    mission: str,
    skill_index: SkillIndex,
    provider: LLMProvider,
    run_dir: Path,
    workspace: Path,
    console: Optional[Console] = None,
    trace: Optional[TraceRecorder] = None,
) -> RunSummary:
    console = console or Console()
    trace = trace or TraceRecorder(run_dir / "trace.jsonl")

    run_dir.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)

    trace.emit("mission.start", {"mission": mission})

    # --- PLAN ---
    available = skill_index.list_compact()
    plan_user = (
        f"MISSION: {mission}\n\n"
        "You are the Supervisor of a small agent company.\n"
        "Based on the mission and the available skills, output a plan in JSON.\n"
        "Rules:\n"
        "- Use ONLY skills from the available list.\n"
        "- 4-8 work_orders is ideal.\n"
        "- Each work_order should list expected output file paths.\n\n"
        "AVAILABLE_SKILLS:\n"
        + _render_skill_list(available)
    )
    trace.emit("plan.request", {"available_skills": len(available)})
    plan_json = provider.complete_json(
        system="You are a planner that produces strict JSON.",
        user=plan_user,
        schema_hint=PLAN_SCHEMA_HINT,
        temperature=0.2,
        max_tokens=1800,
    )
    trace.emit("plan.response", {"raw": plan_json})
    plan = Plan.model_validate(plan_json)
    _safe_write_text(run_dir / "plan.json", json.dumps(plan.model_dump(), ensure_ascii=False, indent=2))

    console.print(f"\n[bold]Plan[/bold] mode={plan.mode} work_orders={len(plan.work_orders)}")

    # --- EXECUTE WORK ORDERS ---
    written: List[Path] = []
    warnings: List[str] = []
    for wo in plan.work_orders:
        trace.emit("work_order.start", {"id": wo.id, "skill": wo.skill, "title": wo.title})
        ref = skill_index.get(wo.skill)
        if not ref:
            w = f"WorkOrder {wo.id} references missing skill: {wo.skill}"
            warnings.append(w)
            trace.emit("work_order.skip", {"id": wo.id, "reason": w})
            continue

        skill_body = skill_index.load_body(wo.skill)
        exec_user = (
            f"MISSION: {mission}\n"
            f"WORK_ORDER: {wo.id} - {wo.title}\n"
            f"SKILL: {wo.skill}\n"
            f"SKILL_DESCRIPTION: {ref.frontmatter.description}\n\n"
            "Follow the SKILL instructions carefully.\n"
            "You MUST generate files as requested by the work order outputs.\n"
            "Return ONLY JSON matching the schema hint.\n\n"
            "WORK_ORDER_OUTPUTS:\n"
            + "\n".join([f"- {o.path}: {o.purpose or ''}" for o in wo.outputs])
            + "\n\n"
            "SKILL_INSTRUCTIONS:\n"
            + skill_body
        )

        trace.emit("skill.exec.request", {"skill": wo.skill, "work_order": wo.id})
        result_json = provider.complete_json(
            system="You are a reliable executor. Output JSON only.",
            user=exec_user,
            schema_hint=EXEC_SCHEMA_HINT,
            temperature=0.2,
            max_tokens=2500,
        )
        trace.emit("skill.exec.response", {"skill": wo.skill, "raw": result_json})

        try:
            result = SkillExecutionResult.model_validate(result_json)
        except Exception as e:
            w = f"Failed to parse execution result for {wo.skill}: {e}"
            warnings.append(w)
            trace.emit("skill.exec.parse_error", {"skill": wo.skill, "error": str(e)})
            continue

        for gf in result.files:
            out_path = workspace / gf.path
            _safe_write_text(out_path, gf.content)
            written.append(out_path)

        warnings.extend(result.warnings or [])

        trace.emit(
            "work_order.done",
            {
                "id": wo.id,
                "skill": wo.skill,
                "files": [f.path for f in result.files],
                "summary": result.summary,
            },
        )

    # --- RUN REPORT ---
    report_lines = []
    report_lines.append(f"# Run Report\n\nMission: {mission}\n")
    report_lines.append("## Plan\n\n")
    report_lines.append("```json\n" + json.dumps(plan.model_dump(), ensure_ascii=False, indent=2) + "\n```\n")
    report_lines.append("## Files written\n\n")
    for p in written:
        report_lines.append(f"- {p.relative_to(workspace)}\n")
    if warnings:
        report_lines.append("\n## Warnings\n\n")
        for w in warnings:
            report_lines.append(f"- {w}\n")
    _safe_write_text(run_dir / "RUN.md", "".join(report_lines))

    trace.emit("mission.done", {"files_written": len(written), "warnings": len(warnings)})

    # Pretty table output
    table = Table(title="Artifacts")
    table.add_column("File")
    table.add_column("Size (bytes)", justify="right")
    for p in written:
        table.add_row(str(p.relative_to(workspace)), str(p.stat().st_size))
    console.print(table)

    console.print(f"\n[green]Done.[/green] Run directory: {run_dir}")
    return RunSummary(run_dir=run_dir, workspace=workspace, plan=plan, written_files=written, warnings=warnings)
