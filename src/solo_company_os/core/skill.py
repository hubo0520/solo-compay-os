from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple

import yaml

from .schema import SkillFrontmatter


FRONTMATTER_BOUNDARY = re.compile(r"^---\s*$")


class SkillParseError(RuntimeError):
    pass


def split_frontmatter(markdown: str) -> Tuple[str, str]:
    """Return (frontmatter_yaml, body_md).

    Expects SKILL.md to start with YAML frontmatter delimited by '---' lines.
    """
    lines = markdown.splitlines()
    if not lines or not FRONTMATTER_BOUNDARY.match(lines[0]):
        raise SkillParseError("SKILL.md must start with '---' YAML frontmatter boundary")

    # find the second boundary
    end = None
    for i in range(1, len(lines)):
        if FRONTMATTER_BOUNDARY.match(lines[i]):
            end = i
            break
    if end is None:
        raise SkillParseError("SKILL.md frontmatter missing closing '---' boundary")

    fm = "\n".join(lines[1:end]).strip() + "\n"
    body = "\n".join(lines[end + 1 :]).lstrip()
    return fm, body


def load_skill_frontmatter(skill_md_path: Path) -> SkillFrontmatter:
    raw = skill_md_path.read_text(encoding="utf-8")
    fm_yaml, _body = split_frontmatter(raw)
    try:
        data = yaml.safe_load(fm_yaml) or {}
    except Exception as e:
        raise SkillParseError(f"Invalid YAML frontmatter in {skill_md_path}: {e}") from e

    try:
        fm = SkillFrontmatter.model_validate(data)
    except Exception as e:
        raise SkillParseError(f"Frontmatter schema validation failed for {skill_md_path}: {e}") from e

    # Spec requirement: name must match parent folder
    parent = skill_md_path.parent.name
    if fm.name != parent:
        raise SkillParseError(
            f"Skill name '{fm.name}' must match directory name '{parent}' for {skill_md_path}"
        )
    return fm


def load_skill_body(skill_md_path: Path) -> str:
    raw = skill_md_path.read_text(encoding="utf-8")
    _fm_yaml, body = split_frontmatter(raw)
    return body
