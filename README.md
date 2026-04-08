# ai-skills

Author AI skills **once**, ship them to four AI coding tools:

- [Claude Code](https://code.claude.com/docs/en/skills) — `.claude/skills/<slug>/SKILL.md` (on-demand)
- [OpenCode](https://opencode.ai/docs/) — `.opencode/skills/<slug>/SKILL.md` (on-demand)
- [Roo Code](https://docs.roocode.com/features/custom-instructions) — `.roo/rules/<NN>-<slug>.md` (always-on workspace rules)
- [OpenAI Codex CLI](https://developers.openai.com/codex/guides/agents-md) — concatenated into `AGENTS.md` (always-on, 32 KiB cap)

The canonical source format is the Claude Code `SKILL.md` dialect. Per-tool adapters under
`scripts/adapters/` transform that source into each target's expected layout. Output lands
in `dist/` (gitignored).

> **Heads up** — Roo Code and Codex have no on-demand skill loading. Skills targeted at
> them are always in the system prompt, and Codex caps the concatenated `AGENTS.md` at
> 32 KiB. The Codex adapter fails the build at 30 KiB so you have headroom. Curate
> `targets:` per skill instead of defaulting all skills to all four tools.

## Quick start

```bash
# 1. Install dependencies (Python 3.10+)
pip install -e .

# 2. Lint your skills
python -m scripts.lint

# 3. Build all targets into dist/
python -m scripts.build --target all

# 4. Install one target into a destination project
python -m scripts.install --target claude --dest ~/my-project
python -m scripts.install --target claude --dest ~/my-project --skill database-access
python -m scripts.install --target claude --dest ~/my-project --dry-run

# 5. Run golden-prompt evals (needs ANTHROPIC_API_KEY)
python -m scripts.eval database-access
python -m scripts.eval database-access --update    # accept new snapshots
```

## Authoring a new skill

1. Copy `skills/_template/SKILL.md` to `skills/<your-slug>/SKILL.md`. The slug must match
   `^[a-z0-9-]+$` and be identical to the directory name.
2. Fill in the YAML frontmatter (`name`, `description`, `targets`, `tags`) and the body.
   See `skills/database-access/SKILL.md` for a worked example.
3. Optional: bundle supporting material under sibling `references/`, `scripts/`, or
   `assets/` directories. They're copied verbatim to Claude Code and OpenCode outputs;
   `references/` files are also flattened into the Roo rules directory so Roo loads them.
4. Optional: add golden prompts at `evals/<your-slug>/prompts.yaml`.
5. `python -m scripts.lint && python -m scripts.build --target all` until clean.

## Repo layout

```
ai-skills/
├── CLAUDE.md                  # guidance for Claude Code sessions in this repo
├── skills/                    # canonical sources (Claude Code SKILL.md dialect)
│   ├── _template/             # copy-this starter
│   └── database-access/       # first real skill
├── evals/<slug>/prompts.yaml  # golden prompts + assertions per skill
├── scripts/
│   ├── lint.py
│   ├── build.py
│   ├── install.py
│   ├── eval.py
│   └── adapters/{base,claude_code,opencode,roo_code,codex}.py
└── dist/                      # gitignored, build output (one subdir per target)
```

See [`CLAUDE.md`](./CLAUDE.md) for the full canonical schema and the asymmetry table that
governs how each adapter maps the canonical SKILL.md into its target's format.
