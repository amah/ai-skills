"""Roo Code adapter.

Roo Code does not parse frontmatter in rule files. The system prompt is built by
appending every file under `.roo/rules/` (workspace-wide) or `.roo/rules-<mode>/`
(mode-specific), in alphabetical basename order, recursively. We strip our YAML
frontmatter, prepend a synthesized header that surfaces the canonical description,
and apply a numeric prefix from `roo_order` to control sort position.

If a skill sets `roo_mode: <slug>`, it routes into `.roo/rules-<slug>/` and we
append a YAML entry to `.roomodes` with the required `slug` / `name` /
`roleDefinition` fields.

Sources:
  https://docs.roocode.com/features/custom-instructions
  https://docs.roocode.com/features/custom-modes
"""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from .base import DIST_DIR, Skill, Target, strip_leading_h1

TARGET = Target.ROO
OUTPUT_ROOT = DIST_DIR / "roo" / ".roo"
ROOMODES_PATH = DIST_DIR / "roo" / ".roomodes"


def _render_body(skill: Skill) -> str:
    """Synthesize a Roo-friendly markdown file (no frontmatter)."""
    desc = skill.description or ""
    body = strip_leading_h1(skill.body).strip()
    return (
        f"# {skill.name}\n\n"
        f"## When to use\n\n{desc}\n\n"
        f"## Instructions\n\n{body}\n"
    )


def _filename(skill: Skill) -> str:
    return f"{skill.roo_order:02d}-{skill.slug}.md"


def emit(skill: Skill) -> list[Path]:
    if skill.roo_mode:
        rules_dir = OUTPUT_ROOT / f"rules-{skill.roo_mode}"
    else:
        rules_dir = OUTPUT_ROOT / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    out_path = rules_dir / _filename(skill)
    out_path.write_text(_render_body(skill), encoding="utf-8")
    written = [out_path]

    # Bundle references/ as additional files in the same rules dir so Roo loads them too.
    # Prefix them with the parent's order + skill slug so they sort right after the main file.
    refs_dir = skill.path / "references"
    if refs_dir.is_dir():
        for ref_file in sorted(refs_dir.rglob("*")):
            if ref_file.is_file():
                rel = ref_file.relative_to(refs_dir)
                ref_name = f"{skill.roo_order:02d}-{skill.slug}-ref-{str(rel).replace('/', '-')}"
                ref_out = rules_dir / ref_name
                ref_out.write_text(ref_file.read_text(encoding="utf-8"), encoding="utf-8")
                written.append(ref_out)

    return written


def _write_roomodes(mode_skills: list[Skill]) -> Path | None:
    """Write a .roomodes YAML file for any skills using roo_mode."""
    if not mode_skills:
        return None
    customModes = []
    for s in mode_skills:
        customModes.append({
            "slug": s.roo_mode,
            "name": s.name,
            "roleDefinition": s.description,
        })
    ROOMODES_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROOMODES_PATH.write_text(
        yaml.safe_dump({"customModes": customModes}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return ROOMODES_PATH


def build(skills: list[Skill]) -> dict:
    eligible = [s for s in skills if TARGET in s.targets]
    roo_root = DIST_DIR / "roo"
    if roo_root.exists():
        shutil.rmtree(roo_root)
    OUTPUT_ROOT.mkdir(parents=True)

    written: list[Path] = []
    for skill in eligible:
        written.extend(emit(skill))

    mode_skills = [s for s in eligible if s.roo_mode]
    roomodes = _write_roomodes(mode_skills)
    if roomodes:
        written.append(roomodes)

    return {"target": TARGET.value, "skills": len(eligible), "files": len(written)}
