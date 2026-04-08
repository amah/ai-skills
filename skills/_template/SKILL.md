---
name: _template
description: |
  Replace me. Describe — in imperative, situational language — when this skill should activate.
  Example: "Use when the user asks to query, inspect, or modify a database."
  Do NOT start with "This skill". Keep under 1024 characters. This is the only thing the model
  sees before it decides whether to load the full body.
version: 0.1.0
targets: [claude, opencode, roo, codex]
tags: []
# roo_order: 50         # optional, controls .roo/rules/ alphabetical sort (00-99)
# roo_mode: <slug>      # optional, routes into .roo/rules-<slug>/ + writes a .roomodes entry
---

# Skill body

The instructions Claude follows once the skill is invoked. Write them as direct guidance to the
assistant, not as prose for a human reader.

## When to apply

Concrete triggers — what the user is trying to accomplish, what shape their request takes.

## Procedure

Numbered steps the assistant should follow.

1. ...
2. ...

## Constraints

Things the assistant must NOT do, with brief reasoning so it can handle edge cases.

## References

Point to sibling files in `references/` for material the assistant should load on demand:

- `references/example.md` — when to read it
