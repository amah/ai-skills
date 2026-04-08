"""Validate canonical SKILL.md files. Exit non-zero on any failure.

Usage:
    python -m scripts.lint
    python -m scripts.lint --include-template
"""
from __future__ import annotations

import argparse
import sys

from scripts.adapters.base import (
    DESCRIPTION_MAX_LEN,
    SKILLS_DIR,
    SLUG_RE,
    Target,
    load_skill,
    load_skills,
)

VALID_TARGETS = {t.value for t in Target}
ALLOWED_ASSET_DIRS = {"references", "scripts", "assets"}
KNOWN_FRONTMATTER_KEYS = {
    "name",
    "description",
    "version",
    "targets",
    "tags",
    "roo_order",
    "roo_mode",
}


def lint_skill(skill) -> list[str]:
    errors: list[str] = []
    fm = skill.frontmatter

    # name
    name = fm.get("name")
    if not name:
        errors.append("missing required field: name")
    else:
        if not SLUG_RE.match(str(name)):
            errors.append(f"name {name!r} must match /^[a-z0-9-]+$/")
        if str(name) != skill.slug:
            errors.append(f"name {name!r} must equal directory name {skill.slug!r}")

    # description
    desc = fm.get("description")
    if not desc:
        errors.append("missing required field: description")
    else:
        desc_str = str(desc).strip()
        if len(desc_str) > DESCRIPTION_MAX_LEN:
            errors.append(f"description is {len(desc_str)} chars, max is {DESCRIPTION_MAX_LEN}")
        lowered = desc_str.lower()
        if lowered.startswith("this skill"):
            errors.append(
                "description must not start with 'This skill' — use imperative/situational language "
                "(e.g. 'Use when the user asks to ...')"
            )

    # targets
    targets = fm.get("targets")
    if targets is not None:
        if not isinstance(targets, list) or not targets:
            errors.append("targets must be a non-empty list")
        else:
            bad = [t for t in targets if t not in VALID_TARGETS]
            if bad:
                errors.append(f"unknown targets: {bad} (valid: {sorted(VALID_TARGETS)})")

    # tags
    tags = fm.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append("tags must be a list")

    # roo_order
    roo_order = fm.get("roo_order")
    if roo_order is not None:
        if not isinstance(roo_order, int) or not (0 <= roo_order <= 99):
            errors.append("roo_order must be an integer between 0 and 99")

    # roo_mode
    roo_mode = fm.get("roo_mode")
    if roo_mode is not None and not SLUG_RE.match(str(roo_mode)):
        errors.append(f"roo_mode {roo_mode!r} must match /^[a-z0-9-]+$/")

    # unknown keys (warn-as-error so typos like `target` get caught)
    unknown = set(fm.keys()) - KNOWN_FRONTMATTER_KEYS
    if unknown:
        errors.append(f"unknown frontmatter keys: {sorted(unknown)}")

    # body must not be empty
    if not skill.body.strip():
        errors.append("skill body is empty")

    # asset dirs sanity: only allowed names, and they must be directories
    for child in skill.path.iterdir():
        if child.name == "SKILL.md":
            continue
        if child.is_dir() and child.name not in ALLOWED_ASSET_DIRS:
            errors.append(
                f"unexpected directory {child.name!r} — only {sorted(ALLOWED_ASSET_DIRS)} are allowed"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint canonical SKILL.md files.")
    parser.add_argument(
        "--include-template",
        action="store_true",
        help="Also lint skills/_template/ (skipped by default).",
    )
    args = parser.parse_args()

    if not SKILLS_DIR.is_dir():
        print(f"error: {SKILLS_DIR} does not exist", file=sys.stderr)
        return 2

    skills = list(load_skills(SKILLS_DIR, include_template=args.include_template))
    if args.include_template:
        # _template intentionally has slug != name; lint it as a real skill anyway
        # by loading it explicitly so the loop sees it.
        pass

    if not skills:
        print("no skills found (did you mean --include-template?)")
        return 0

    total_errors = 0
    for skill in skills:
        try:
            errs = lint_skill(skill)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {skill.slug}: {e}")
            total_errors += 1
            continue
        if errs:
            for e in errs:
                print(f"FAIL {skill.slug}: {e}")
            total_errors += len(errs)
        else:
            print(f"OK   {skill.slug}")

    if total_errors:
        print(f"\n{total_errors} error(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
