from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from rich.console import Console

from .schema import SkillFrontmatter, SkillRef
from .skill import SkillParseError, load_skill_body, load_skill_frontmatter


DEFAULT_SKILL_DIRS: Tuple[str, ...] = (
    ".agents/skills",
    ".github/skills",
    ".claude/skills",
    "skills",
    "~/.claude/skills",
    "~/.codex/skills",
)


@dataclass
class DiscoveryReport:
    roots_scanned: List[Path]
    skills: List[SkillRef]
    errors: List[str]


class SkillIndex:
    def __init__(self, skills: Sequence[SkillRef]):
        self._skills_by_name: Dict[str, SkillRef] = {s.frontmatter.name: s for s in skills}

    @property
    def skills(self) -> List[SkillRef]:
        return list(self._skills_by_name.values())

    def get(self, name: str) -> Optional[SkillRef]:
        return self._skills_by_name.get(name)

    def require(self, name: str) -> SkillRef:
        s = self.get(name)
        if not s:
            raise KeyError(f"Skill not found: {name}")
        return s

    def load_body(self, name: str) -> str:
        ref = self.require(name)
        return load_skill_body(ref.skill_md)

    def list_compact(self) -> List[Tuple[str, str]]:
        return sorted(
            [(s.frontmatter.name, s.frontmatter.description) for s in self.skills],
            key=lambda x: x[0],
        )


def _expand_dir(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p))).resolve()


def discover_skills(
    roots: Optional[Iterable[str]] = None,
    console: Optional[Console] = None,
) -> DiscoveryReport:
    console = console or Console()
    roots_in = list(roots) if roots is not None else list(DEFAULT_SKILL_DIRS)

    roots_scanned: List[Path] = []
    skills: List[SkillRef] = []
    errors: List[str] = []

    seen_names: set[str] = set()

    for root_str in roots_in:
        root = _expand_dir(root_str)
        if not root.exists() or not root.is_dir():
            continue
        roots_scanned.append(root)

        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            skill_md = child / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                fm = load_skill_frontmatter(skill_md)
                if fm.name in seen_names:
                    errors.append(
                        f"Duplicate skill name '{fm.name}' found at {skill_md} (already loaded)"
                    )
                    continue
                seen_names.add(fm.name)
                skills.append(SkillRef(folder=child, skill_md=skill_md, frontmatter=fm))
            except SkillParseError as e:
                errors.append(str(e))

    return DiscoveryReport(roots_scanned=roots_scanned, skills=skills, errors=errors)


def validate_skills(roots: Optional[Iterable[str]] = None) -> DiscoveryReport:
    # discovery already validates; this just returns a report
    return discover_skills(roots=roots)
