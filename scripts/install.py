"""Copy a built dist/<target>/ tree into a destination directory.

Usage:
    python -m scripts.install --target claude --dest ~/my-project
    python -m scripts.install --target claude --dest ~/my-project --skill database-access
    python -m scripts.install --target claude --dest ~/my-project --dry-run
    python -m scripts.install --target codex  --dest ~/my-project   # writes AGENTS.md at dest root

The destination is treated as a project root. The script copies the layout from
`dist/<target>/` (e.g. `dist/claude/.claude/skills/...`) preserving its structure under <dest>.

This script does NOT run the build — run `python -m scripts.build --target <t>` first.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from scripts.adapters import Target
from scripts.adapters.base import DIST_DIR


def _target_root(target: Target) -> Path:
    return DIST_DIR / target.value


def _iter_install_files(src_root: Path, skill: str | None) -> list[tuple[Path, Path]]:
    """Yield (src_file, rel_path_within_dest) tuples for the install."""
    if not src_root.is_dir():
        raise FileNotFoundError(
            f"{src_root} does not exist — run `python -m scripts.build --target {src_root.name}` first"
        )

    pairs: list[tuple[Path, Path]] = []
    for src in src_root.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(src_root)
        if skill is not None:
            # Filter to files belonging to the requested skill. We match on either
            # a path component equal to the slug (claude/opencode layout) or on
            # the filename containing the slug (roo's `NN-<slug>.md` layout).
            in_path = skill in rel.parts
            in_name = skill in rel.name
            if not (in_path or in_name):
                continue
        pairs.append((src, rel))
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(description="Install built skills into a destination project.")
    parser.add_argument("--target", required=True, choices=[t.value for t in Target])
    parser.add_argument("--dest", required=True, type=Path, help="Destination project root.")
    parser.add_argument("--skill", default=None, help="Install only this skill slug.")
    parser.add_argument("--dry-run", action="store_true", help="List what would be copied; write nothing.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files at the destination.")
    args = parser.parse_args()

    target = Target(args.target)
    src_root = _target_root(target)
    dest_root: Path = args.dest.expanduser().resolve()

    try:
        pairs = _iter_install_files(src_root, args.skill)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if not pairs:
        if args.skill:
            print(f"no files for skill {args.skill!r} under {src_root}", file=sys.stderr)
        else:
            print(f"no files under {src_root}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"DRY RUN — would copy {len(pairs)} file(s) from {src_root} to {dest_root}:")
        for _, rel in pairs:
            print(f"  {dest_root / rel}")
        return 0

    if not dest_root.exists():
        print(f"error: destination {dest_root} does not exist", file=sys.stderr)
        return 2
    if not dest_root.is_dir():
        print(f"error: destination {dest_root} is not a directory", file=sys.stderr)
        return 2

    written = 0
    skipped = 0
    for src, rel in pairs:
        dest_file = dest_root / rel
        if dest_file.exists() and not args.force:
            print(f"SKIP {rel} (exists; use --force to overwrite)")
            skipped += 1
            continue
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_file)
        print(f"COPY {rel}")
        written += 1

    print(f"\n{written} file(s) written, {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
