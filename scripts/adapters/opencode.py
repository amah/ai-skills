"""OpenCode adapter: canonical SKILL.md → dist/opencode/.opencode/skills/<slug>/.

OpenCode now ships a first-class `.opencode/skills/` directory alongside `agents/`,
`commands/`, `modes/`. The format is close enough to Claude Code's that we emit the
same structure with the same frontmatter (minus our local-only fields).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .base import DIST_DIR, Skill, Target, serialize_frontmatter

TARGET = Target.OPENCODE
OUTPUT_ROOT = DIST_DIR / "opencode" / ".opencode" / "skills"


def emit(skill: Skill) -> list[Path]:
    out_dir = OUTPUT_ROOT / skill.slug
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    skill_md = out_dir / "SKILL.md"
    skill_md.write_text(
        serialize_frontmatter(skill.public_frontmatter(), skill.body),
        encoding="utf-8",
    )
    written = [skill_md]

    for asset_dir in skill.asset_dirs():
        dest = out_dir / asset_dir.name
        shutil.copytree(asset_dir, dest)
        written.extend(p for p in dest.rglob("*") if p.is_file())

    return written


def build(skills: list[Skill]) -> dict:
    eligible = [s for s in skills if TARGET in s.targets]
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)
    written: list[Path] = []
    for skill in eligible:
        written.extend(emit(skill))
    return {"target": TARGET.value, "skills": len(eligible), "files": len(written)}
