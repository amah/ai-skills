"""Build canonical skills into per-target dist trees.

Usage:
    python -m scripts.build                          # all targets
    python -m scripts.build --target claude          # one target
    python -m scripts.build --target claude opencode # subset
"""
from __future__ import annotations

import argparse
import sys

from scripts.adapters import Target, load_skills
from scripts.adapters import claude_code, codex, opencode, roo_code
from scripts.adapters.base import SKILLS_DIR
from scripts.adapters.codex import CodexBudgetError

ADAPTERS = {
    Target.CLAUDE: claude_code,
    Target.OPENCODE: opencode,
    Target.ROO: roo_code,
    Target.CODEX: codex,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build skills for one or more target tools.")
    parser.add_argument(
        "--target",
        nargs="+",
        choices=[t.value for t in Target] + ["all"],
        default=["all"],
        help="Targets to build (default: all).",
    )
    args = parser.parse_args()

    if "all" in args.target:
        targets = Target.all()
    else:
        targets = [Target(t) for t in args.target]

    if not SKILLS_DIR.is_dir():
        print(f"error: {SKILLS_DIR} does not exist", file=sys.stderr)
        return 2

    skills = list(load_skills(SKILLS_DIR))
    if not skills:
        print("no skills found")
        return 0

    print(f"loaded {len(skills)} skill(s): {', '.join(s.slug for s in skills)}")
    rc = 0
    for target in targets:
        adapter = ADAPTERS[target]
        try:
            result = adapter.build(skills)
        except CodexBudgetError as e:
            print(f"FAIL {target.value}: {e}", file=sys.stderr)
            rc = 1
            continue
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {target.value}: {type(e).__name__}: {e}", file=sys.stderr)
            rc = 1
            continue
        bytes_str = f", {result['bytes']} bytes" if "bytes" in result else ""
        print(f"OK   {target.value}: {result['skills']} skill(s), {result['files']} file(s){bytes_str}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
