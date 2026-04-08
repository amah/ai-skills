"""Claude Code adapter: canonical SKILL.md → dist/claude/.claude/skills/<slug>/."""
from __future__ import annotations

import shutil
from pathlib import Path

from .base import DIST_DIR, Skill, Target, serialize_frontmatter

TARGET = Target.CLAUDE
OUTPUT_ROOT = DIST_DIR / "claude" / ".claude" / "skills"


def emit(skill: Skill) -> list[Path]:
    """Write skill into the Claude Code dist tree. Returns paths written."""
    out_dir = OUTPUT_ROOT / skill.slug
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    # SKILL.md with local-only fields stripped
    skill_md = out_dir / "SKILL.md"
    skill_md.write_text(
        serialize_frontmatter(skill.public_frontmatter(), skill.body),
        encoding="utf-8",
    )
    written = [skill_md]

    # Copy sibling asset directories verbatim
    for asset_dir in skill.asset_dirs():
        dest = out_dir / asset_dir.name
        shutil.copytree(asset_dir, dest)
        written.extend(p for p in dest.rglob("*") if p.is_file())

    return written


def build(skills: list[Skill]) -> dict:
    """Build all eligible skills into the Claude Code dist tree."""
    eligible = [s for s in skills if TARGET in s.targets]
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)
    written: list[Path] = []
    for skill in eligible:
        written.extend(emit(skill))
    return {"target": TARGET.value, "skills": len(eligible), "files": len(written)}
