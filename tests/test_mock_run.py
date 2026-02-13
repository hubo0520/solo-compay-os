from pathlib import Path

from solo_company_os.core.orchestrator import run_mission
from solo_company_os.core.providers.mock import MockProvider
from solo_company_os.core.skill_index import SkillIndex, discover_skills


def test_mock_run_generates_files(tmp_path: Path):
    report = discover_skills(roots=[".agents/skills"])
    idx = SkillIndex(report.skills)
    provider = MockProvider()
    run_dir = tmp_path / "run"
    workspace = run_dir / "workspace"

    summary = run_mission(
        mission="Build a runnable demo landing page with FastAPI",
        skill_index=idx,
        provider=provider,
        run_dir=run_dir,
        workspace=workspace,
    )

    # Ensure at least PRD exists
    assert (workspace / "docs/PRD.md").exists()
    # Build mode should generate app
    assert (workspace / "app/main.py").exists()
