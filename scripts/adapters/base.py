"""Shared model + loader for canonical SKILL.md files.

A canonical skill lives at `skills/<slug>/SKILL.md` with YAML frontmatter and a markdown body.
Adapters consume the parsed `Skill` and emit per-target output trees.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
DIST_DIR = REPO_ROOT / "dist"

SLUG_RE = re.compile(r"^[a-z0-9-]+$")
DESCRIPTION_MAX_LEN = 1024
# Local-only frontmatter fields that must NOT be emitted to Claude Code / OpenCode output.
LOCAL_FIELDS = {"targets", "tags", "roo_order", "roo_mode"}


class Target(str, Enum):
    CLAUDE = "claude"
    OPENCODE = "opencode"
    ROO = "roo"
    CODEX = "codex"

    @classmethod
    def all(cls) -> list["Target"]:
        return list(cls)


@dataclass
class Skill:
    slug: str
    path: Path  # path to the skill directory (skills/<slug>/)
    frontmatter: dict
    body: str

    # --- accessors ---
    @property
    def name(self) -> str:
        return self.frontmatter.get("name", self.slug)

    @property
    def description(self) -> str:
        return (self.frontmatter.get("description") or "").strip()

    @property
    def targets(self) -> list[Target]:
        raw = self.frontmatter.get("targets")
        if raw is None:
            return Target.all()
        return [Target(t) for t in raw]

    @property
    def tags(self) -> list[str]:
        return list(self.frontmatter.get("tags") or [])

    @property
    def roo_order(self) -> int:
        return int(self.frontmatter.get("roo_order", 50))

    @property
    def roo_mode(self) -> str | None:
        v = self.frontmatter.get("roo_mode")
        return str(v) if v else None

    def asset_dirs(self) -> list[Path]:
        """Sibling directories that should be copied alongside SKILL.md (Claude/OpenCode)."""
        return [d for d in (self.path / sub for sub in ("references", "scripts", "assets")) if d.is_dir()]

    def public_frontmatter(self) -> dict:
        """Frontmatter with local-only extension fields stripped."""
        return {k: v for k, v in self.frontmatter.items() if k not in LOCAL_FIELDS}


def parse_skill_md(skill_md: Path) -> tuple[dict, str]:
    """Parse a SKILL.md file into (frontmatter, body)."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{skill_md}: missing YAML frontmatter (must start with '---')")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{skill_md}: malformed frontmatter (no closing '---')")
    fm_text, body = parts[1], parts[2]
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"{skill_md}: invalid YAML frontmatter: {e}") from e
    if not isinstance(fm, dict):
        raise ValueError(f"{skill_md}: frontmatter must be a YAML mapping")
    return fm, body.lstrip("\n")


def load_skill(skill_dir: Path) -> Skill:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"{skill_dir}: missing SKILL.md")
    fm, body = parse_skill_md(skill_md)
    return Skill(slug=skill_dir.name, path=skill_dir, frontmatter=fm, body=body)


def load_skills(skills_dir: Path = SKILLS_DIR, *, include_template: bool = False) -> Iterator[Skill]:
    """Yield every skill under skills/. Hidden dirs and `_template` are skipped by default."""
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if child.name == "_template" and not include_template:
            continue
        yield load_skill(child)


def strip_leading_h1(body: str) -> str:
    """Drop a leading `# Heading` line (and a blank line after it) from a body string.

    Used by adapters that wrap the body in their own heading (Codex, Roo Code) to avoid
    a duplicated title in the rendered output.
    """
    lines = body.lstrip("\n").splitlines()
    if not lines or not lines[0].startswith("# "):
        return body
    rest = lines[1:]
    while rest and not rest[0].strip():
        rest = rest[1:]
    return "\n".join(rest)


def serialize_frontmatter(fm: dict, body: str) -> str:
    """Re-emit a SKILL.md text from a frontmatter dict and body string."""
    fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    body_clean = body.lstrip("\n")
    return f"---\n{fm_text}\n---\n\n{body_clean}"
