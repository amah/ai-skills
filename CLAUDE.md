# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo authors AI skills **once** in a canonical format and ships them to four target tools:

- **Claude Code** (`.claude/skills/<slug>/SKILL.md`)
- **OpenCode** (`.opencode/skills/<slug>/SKILL.md`)
- **Roo Code** (`.roo/rules/<NN>-<slug>.md`)
- **OpenAI Codex CLI** (concatenated into `AGENTS.md`)

The canonical source is the Claude Code `SKILL.md` dialect (directory-per-skill, YAML frontmatter with `name` + `description`, optional `references/`/`scripts/`/`assets/` siblings). Per-tool adapters under `scripts/adapters/` transform that source into each target's expected layout. Output lands in `dist/` (gitignored).

## Critical asymmetry: not every target supports on-demand skill loading

| Target      | Loading model                                             | Implication for authors |
|-------------|-----------------------------------------------------------|-------------------------|
| Claude Code | On-demand via `description`                               | 1:1 copy of canonical. |
| OpenCode    | On-demand (first-class `.opencode/skills/` directory)     | Near-1:1; description matters. |
| Roo Code    | **Always-on** workspace rules, alphabetical file order    | No frontmatter parsed; description is folded into the body. |
| Codex CLI   | **Always-on**, single concatenated `AGENTS.md`, **32 KiB cap** by default (`project_doc_max_bytes`) | Every codex-targeted skill goes into the same file — **30 KiB build budget** is enforced. |

When adding a skill, decide explicitly which targets it ships to via the `targets:` frontmatter field. Defaulting all skills to all four targets will eventually blow the Codex budget.

## Canonical SKILL.md schema

```yaml
---
name: my-skill                    # required, /^[a-z0-9-]+$/, must equal directory name
description: |                    # required, ≤1024 chars; the only thing the model sees before loading
  Use when ... (imperative/situational; do NOT start with "This skill")
version: 0.1.0                    # optional, semver
targets: [claude, opencode, roo, codex]   # optional, defaults to all four
tags: [tool-use, database]        # optional, used for grouping in AGENTS.md
roo_order: 50                     # optional, integer 0-99, controls .roo/rules/ alphabetical sort
roo_mode: <slug>                  # optional, routes into .roo/rules-<slug>/ + writes a .roomodes entry
---

# body — instructions the assistant follows once the skill is invoked
```

`name`, `description`, and the body are passed through to Claude Code unchanged. The other fields are local extensions consumed by adapters and stripped before emitting Claude/OpenCode output.

## Adding a new skill

1. Copy `skills/_template/SKILL.md` to `skills/<your-slug>/SKILL.md`. Slug must match `^[a-z0-9-]+$` and equal the directory name.
2. Optional supporting files go in sibling `references/`, `scripts/`, or `assets/` directories.
3. Run `python -m scripts.lint` until clean.
4. Run `python -m scripts.build --target all` and inspect `dist/` to confirm each adapter emitted what you expected.
5. (Optional) Add a `evals/<your-slug>/prompts.yaml` with golden prompts and run `python -m scripts.eval <your-slug>`.

## Commands

```bash
python -m scripts.lint                                  # validate all skills
python -m scripts.build --target all                    # build all targets into dist/
python -m scripts.build --target claude                 # build a single target
python -m scripts.install --target claude --dest <dir>  # copy dist/claude/ tree into <dir>
python -m scripts.install --target claude --dest <dir> --skill <slug>  # install one skill
python -m scripts.install --target claude --dest <dir> --dry-run       # preview without writing
python -m scripts.eval <skill-slug>                     # run golden-prompt evals (needs ANTHROPIC_API_KEY)
python -m scripts.eval <skill-slug> --update            # accept new snapshots
```

## Hard constraints

- The Codex adapter **fails the build** if the concatenated `AGENTS.md` exceeds 30 KiB (2 KiB headroom under Codex's 32 KiB default cap). When this fires, narrow `targets:` on the largest skills rather than raising the cap.
- Roo Code does not parse frontmatter. The Roo adapter strips it and synthesizes a `## When to use` / `## Instructions` header from the canonical `description` and body. Don't write Roo-specific frontmatter expecting it to survive.
- Description length is capped at 1024 characters during lint. Descriptions starting with "This skill" are rejected — they should be imperative/situational so Claude Code's loader can match them against user intent.
