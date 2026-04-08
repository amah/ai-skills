"""Codex CLI adapter.

Codex reads `AGENTS.md` files (always-on, single concatenated instruction set) with a
default 32 KiB cap (`project_doc_max_bytes`). We concatenate every codex-targeted skill
into a single `dist/codex/AGENTS.md`, grouped by tag for legibility, and fail the build
if the result exceeds 30 KiB (2 KiB headroom).

Source: https://developers.openai.com/codex/guides/agents-md
"""
from __future__ import annotations

import shutil
from collections import defaultdict
from pathlib import Path

from .base import DIST_DIR, Skill, Target, strip_leading_h1

TARGET = Target.CODEX
OUTPUT_ROOT = DIST_DIR / "codex"
OUTPUT_FILE = OUTPUT_ROOT / "AGENTS.md"

# Codex's default cap is 32 KiB. Leave 2 KiB headroom for safety + future growth.
SOFT_CAP_BYTES = 30 * 1024


class CodexBudgetError(RuntimeError):
    pass


def _render_skill(skill: Skill) -> str:
    """Render a single skill as a markdown section under a `## ` heading."""
    desc = skill.description
    body = strip_leading_h1(skill.body).strip()
    return f"## {skill.name}\n\n{desc}\n\n{body}\n"


def _group_by_tag(skills: list[Skill]) -> dict[str, list[Skill]]:
    """Group skills by their first tag (or 'misc' if untagged)."""
    groups: dict[str, list[Skill]] = defaultdict(list)
    for s in skills:
        key = s.tags[0] if s.tags else "misc"
        groups[key].append(s)
    return dict(sorted(groups.items()))


def build(skills: list[Skill]) -> dict:
    eligible = [s for s in skills if TARGET in s.targets]
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)

    if not eligible:
        OUTPUT_FILE.write_text("# AGENTS.md\n\n_No skills targeted at codex._\n", encoding="utf-8")
        return {"target": TARGET.value, "skills": 0, "files": 1, "bytes": OUTPUT_FILE.stat().st_size}

    parts: list[str] = [
        "# AGENTS.md",
        "",
        "_Generated from canonical skills in `skills/` by `scripts/adapters/codex.py`._",
        "",
    ]
    for tag, group in _group_by_tag(eligible).items():
        parts.append(f"# {tag}")
        parts.append("")
        for skill in group:
            parts.append(_render_skill(skill))

    content = "\n".join(parts).rstrip() + "\n"
    size = len(content.encode("utf-8"))
    if size > SOFT_CAP_BYTES:
        ranked = sorted(
            ((len(_render_skill(s).encode("utf-8")), s.slug) for s in eligible),
            reverse=True,
        )
        biggest = "\n".join(f"  - {slug}: {sz} bytes" for sz, slug in ranked[:5])
        raise CodexBudgetError(
            f"AGENTS.md is {size} bytes, over the {SOFT_CAP_BYTES}-byte soft cap "
            f"(Codex default project_doc_max_bytes is 32 KiB).\n"
            f"Drop the largest skills from the `codex` target, or split them.\n"
            f"Largest skills:\n{biggest}"
        )

    OUTPUT_FILE.write_text(content, encoding="utf-8")
    return {"target": TARGET.value, "skills": len(eligible), "files": 1, "bytes": size}
