from pathlib import Path

from solo_company_os.core.skill_index import discover_skills, SkillIndex


def test_discover_local_skills():
    report = discover_skills(roots=[".agents/skills"])
    assert not report.errors, f"Expected no skill errors, got: {report.errors}"
    idx = SkillIndex(report.skills)
    assert idx.get("pm-prd") is not None
    assert idx.get("eng-fastapi-starter") is not None
