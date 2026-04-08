"""Run golden-prompt evals for one skill against the Anthropic API.

Usage:
    python -m scripts.eval database-access
    python -m scripts.eval database-access --model claude-haiku-4-5-20251001
    python -m scripts.eval database-access --update      # accept new snapshots

Reads:  evals/<slug>/prompts.yaml
Writes: evals/<slug>/snapshots/<case>.txt  (gitignored)

Assertion types in prompts.yaml:
  contains: substring (case-insensitive)
  regex:    Python regex (case-insensitive, multiline, dotall)
  judge:    natural-language judge prompt; Haiku is asked PASS or FAIL with rationale

Skipped (exit 0) if ANTHROPIC_API_KEY is unset, so contributors without keys can still
run lint/build in CI.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

from scripts.adapters.base import REPO_ROOT, load_skill

EVALS_DIR = REPO_ROOT / "evals"
DEFAULT_MODEL = "claude-opus-4-5"   # can be overridden via --model
JUDGE_MODEL = "claude-haiku-4-5-20251001"


def _load_cases(slug: str) -> list[dict]:
    path = EVALS_DIR / slug / "prompts.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no eval cases at {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cases = data.get("cases") or []
    if not cases:
        raise ValueError(f"{path}: no cases defined")
    return cases


def _check_contains(needle: str, response: str) -> tuple[bool, str]:
    ok = needle.lower() in response.lower()
    return ok, f"contains {needle!r}"


def _check_regex(pattern: str, response: str) -> tuple[bool, str]:
    flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
    ok = re.search(pattern, response, flags) is not None
    return ok, f"regex {pattern!r}"


def _check_judge(client, judge_prompt: str, model_response: str) -> tuple[bool, str]:
    """Ask Haiku to PASS/FAIL the response against the judge prompt."""
    full = (
        f"{judge_prompt}\n\n"
        f"--- ASSISTANT RESPONSE TO JUDGE ---\n{model_response}\n--- END RESPONSE ---\n\n"
        f"Reply with exactly PASS or FAIL on the first line, then one sentence of rationale."
    )
    msg = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": full}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text").strip()
    first_line = text.splitlines()[0].strip().upper() if text else ""
    ok = first_line.startswith("PASS")
    return ok, f"judge → {text[:200]}"


def _run_case(client, model: str, system_prompt: str, case: dict) -> tuple[bool, str, list[str]]:
    msg = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": case["prompt"]}],
    )
    response = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")

    results: list[str] = []
    all_ok = True
    for assertion in case.get("expect", []) or []:
        if "contains" in assertion:
            ok, label = _check_contains(assertion["contains"], response)
        elif "regex" in assertion:
            ok, label = _check_regex(assertion["regex"], response)
        elif "judge" in assertion:
            ok, label = _check_judge(client, assertion["judge"], response)
        else:
            ok, label = False, f"unknown assertion {assertion!r}"
        results.append(("PASS" if ok else "FAIL") + " " + label)
        if not ok:
            all_ok = False

    return all_ok, response, results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run golden-prompt evals for one skill.")
    parser.add_argument("slug", help="Skill slug under evals/.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model to test against.")
    parser.add_argument("--update", action="store_true", help="Accept new snapshots without diff.")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — skipping eval (exit 0)")
        return 0

    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        print("anthropic SDK not installed — run `pip install -e .`", file=sys.stderr)
        return 2

    skill_dir = REPO_ROOT / "skills" / args.slug
    skill = load_skill(skill_dir)
    cases = _load_cases(args.slug)

    snapshots_dir = EVALS_DIR / args.slug / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    client = Anthropic()
    system_prompt = skill.body

    failures = 0
    for case in cases:
        name = case["name"]
        print(f"\n=== {name} ===")
        try:
            ok, response, results = _run_case(client, args.model, system_prompt, case)
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR: {type(e).__name__}: {e}")
            failures += 1
            continue

        snap_path = snapshots_dir / f"{name}.txt"
        if args.update or not snap_path.exists():
            snap_path.write_text(response, encoding="utf-8")
            print(f"  snapshot {'updated' if snap_path.exists() else 'written'} → {snap_path}")
        else:
            existing = snap_path.read_text(encoding="utf-8")
            if existing != response:
                print(f"  SNAPSHOT DRIFT (use --update to accept)")
                ok = False

        for r in results:
            print(f"  {r}")
        if not ok:
            failures += 1

    if failures:
        print(f"\n{failures} case(s) failed", file=sys.stderr)
        return 1
    print("\nall cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
