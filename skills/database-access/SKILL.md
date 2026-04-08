---
name: database-access
description: |
  Use when the user asks to query, inspect, or modify a database — SQLite, Postgres, MySQL,
  or any SQL engine. Enforces safe-by-default reads, parameterized statements, transactional
  writes with explicit confirmation for destructive operations, and engine-specific gotchas.
version: 0.1.0
targets: [claude, opencode, roo, codex]
tags: [tool-use, database]
---

# database-access

You are helping the user interact with a SQL database. Treat the database as production unless
the user has explicitly said otherwise. The cost of a wrong `UPDATE` or `DROP` is high and not
always reversible — earn the right to mutate state.

## When to apply

The user's request involves running SQL or inspecting a database:

- "Query the users table for ..."
- "Update the status column where ..."
- "How many rows in ...?"
- "Drop the old migrations table"
- "Connect to the staging database and ..."

## Procedure

1. **Confirm the engine and connection target before issuing any statement.** Ask which engine
   (SQLite / Postgres / MySQL / other) and which environment (local / staging / production) if
   it isn't already obvious from the conversation or files in the working directory. Do not
   guess from a `DATABASE_URL` you found in `.env` — confirm with the user that you should use it.

2. **Default to a read-only session.** For Postgres, prefer `SET TRANSACTION READ ONLY` or a
   read-only role. For SQLite, open with `mode=ro`. For MySQL, prefer a read-only user. Only
   escalate to a writable session when the user has explicitly asked for a write and you have
   shown them the exact statement you intend to run.

3. **Always parameterize values.** Never interpolate user-supplied or assistant-generated values
   into SQL strings. Use the driver's parameter binding (`?`, `$1`, `%s`, named parameters) and
   pass values separately. This applies even for "obviously safe" values like integers — the
   habit matters more than the immediate risk.

4. **For destructive statements** (`UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `MERGE`):
   1. Run a `SELECT` first that returns the rows that *would* be affected (or `EXPLAIN` for
      schema changes). Show the user the count and a sample.
   2. Wrap the mutation in an explicit transaction (`BEGIN; ... ROLLBACK;` or `COMMIT;`).
   3. Show the user the exact statement you intend to run, and wait for an explicit
      confirmation token (e.g. they reply "yes, commit" or "go ahead"). Do not infer consent
      from earlier turns.
   4. After execution, report the actual row count and offer to `ROLLBACK` if the number
      diverges from the dry-run.

5. **Never run schema-changing or data-deleting statements without a backup path.** For
   production targets, ask the user to confirm a recent backup exists or to take one (e.g.
   `pg_dump`, `mysqldump`, `.backup` for SQLite) before proceeding.

6. **When listing query results**, paginate. Cap initial output at 50 rows; offer to fetch more.
   Truncate wide columns to a reasonable width and tell the user you've truncated.

## Constraints

- **Do not** use string concatenation, f-strings, or `format()` to build SQL with values.
- **Do not** issue `DROP DATABASE`, `DROP SCHEMA`, or `TRUNCATE` against any target the user
  has identified as production, even with confirmation, without a second explicit confirmation
  on a separate turn.
- **Do not** silently auto-commit. If the driver defaults to autocommit, disable it for this
  session.
- **Do not** read from `.pgpass`, `~/.my.cnf`, or environment variables for credentials without
  telling the user which credential source you're using.
- **Do not** export query results to a file outside the current working directory without
  confirming the path with the user.

## References

- `references/safe-query-patterns.md` — engine-specific gotchas (SQLite vs Postgres vs MySQL),
  parameter binding syntax, and read-only session setup. Read this when the user picks an
  engine you haven't worked with this session.
