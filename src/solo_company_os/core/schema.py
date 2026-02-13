from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SkillFrontmatter(BaseModel):
    """YAML frontmatter as defined by the Agent Skills specification.

    We validate the required fields (name, description) and a subset of optional ones.
    """

    name: str = Field(..., description="Skill identifier (kebab-case), must match parent folder.")
    description: str = Field(..., description="What the skill does and when to use it.")
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    allowed_tools: Optional[str] = Field(default=None, alias="allowed-tools")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not (1 <= len(v) <= 64):
            raise ValueError("name must be 1-64 characters")
        if v.startswith("-") or v.endswith("-") or "--" in v:
            raise ValueError("name must not start/end with '-' and must not contain '--'")
        # spec says lowercase alphanumerics + hyphen only; we allow unicode lowercase to be lenient,
        # but enforce a-z0-9- for compatibility with most runtimes.
        import re

        if not re.fullmatch(r"[a-z0-9-]+", v):
            raise ValueError("name must match [a-z0-9-]+ (kebab-case)")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description must be non-empty")
        if len(v) > 1024:
            raise ValueError("description must be <= 1024 chars")
        return v


@dataclass(frozen=True)
class SkillRef:
    """A discovered skill on disk."""

    folder: Path
    skill_md: Path
    frontmatter: SkillFrontmatter


class PlannedFile(BaseModel):
    path: str
    purpose: Optional[str] = None


class WorkOrder(BaseModel):
    id: str
    title: str
    skill: str = Field(..., description="Skill name to activate")
    outputs: List[PlannedFile] = Field(default_factory=list)
    notes: Optional[str] = None


class Plan(BaseModel):
    mode: str = Field(..., description="learn|build|mixed")
    work_orders: List[WorkOrder]
    assumptions: List[str] = Field(default_factory=list)


class GeneratedFile(BaseModel):
    path: str
    content: str


class SkillExecutionResult(BaseModel):
    files: List[GeneratedFile] = Field(default_factory=list)
    summary: str = ""
    warnings: List[str] = Field(default_factory=list)
