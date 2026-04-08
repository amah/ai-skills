# Safe query patterns by engine

Engine-specific notes for the `database-access` skill. Read this when the user picks an engine
you haven't already worked with in the current session.

## SQLite

- **Read-only mode**: open with a URI connection string and `mode=ro`:
  ```
  sqlite3.connect("file:app.db?mode=ro", uri=True)
  ```
- **Parameter binding**: positional `?` or named `:name`. Pass a tuple/dict as the second arg
  to `execute`.
- **Transactions**: SQLite's Python driver auto-commits in `isolation_level=""` mode by default.
  For destructive work, set `isolation_level=None` and issue `BEGIN` / `COMMIT` / `ROLLBACK`
  yourself, or use `with conn:` which commits on success and rolls back on exception.
- **Backup**: `.backup target.db` from the `sqlite3` shell, or `conn.backup(target_conn)` from
  Python. Cheap; always do it before destructive work.
- **Gotcha**: SQLite does not enforce column types by default ("type affinity"). A `TEXT`
  column will silently accept integers. Validate at the application layer.

## Postgres

- **Read-only session**: `SET TRANSACTION READ ONLY;` after `BEGIN`, or connect as a role with
  no write grants. The `default_transaction_read_only` server parameter is the strongest form.
- **Parameter binding**: `$1`, `$2`, ... in raw SQL; `%s` in psycopg / psycopg2; named
  parameters via `psycopg.sql` or SQLAlchemy. Never use Python `%` formatting.
- **Transactions**: psycopg defaults to a transaction per cursor in older versions. With
  psycopg3, use `with conn.transaction():`. Always disable autocommit for destructive work.
- **Backup**: `pg_dump -Fc dbname > backup.dump` for a single database, `pg_dumpall` for the
  whole cluster. For point-in-time, the user needs WAL archiving — ask if they have it.
- **Gotcha**: `DELETE FROM big_table` without a `WHERE` clause is not the same as
  `TRUNCATE big_table` — the former is logged row-by-row and slow, the latter is fast but
  resets sequences. Confirm which the user wants.
- **Gotcha**: identifier quoting uses `"double quotes"`, value quoting uses `'single quotes'`.
  Mixing them silently changes meaning.

## MySQL / MariaDB

- **Read-only session**: connect as a `SELECT`-only user, or `SET SESSION TRANSACTION READ ONLY;`.
  Note that `read_only` server variable only blocks writes for non-`SUPER` users.
- **Parameter binding**: `%s` in `mysql-connector-python` and `PyMySQL`; named parameters via
  `%(name)s`. Do not use the driver's `format()`-style escaping helpers as a substitute.
- **Transactions**: InnoDB tables are transactional; MyISAM tables are not. Check
  `SHOW TABLE STATUS` if you're unsure — wrapping a MyISAM mutation in `BEGIN`/`ROLLBACK`
  silently does nothing.
- **Backup**: `mysqldump --single-transaction --routines --triggers dbname > backup.sql`. The
  `--single-transaction` flag is critical for InnoDB consistency without locking.
- **Gotcha**: `UPDATE` without `WHERE` is allowed by default and will rewrite every row. Some
  clients enable `--safe-updates` (`sql_safe_updates=1`) which blocks this — you can't rely on
  it being on.
- **Gotcha**: MySQL's default collation can make string comparisons case-insensitive. A
  `WHERE name = 'Foo'` query may match `'foo'` and `'FOO'`.

## Universal: dry-run pattern for destructive statements

Before any `UPDATE` / `DELETE`:

```sql
-- 1. Dry run: count and sample what will change
SELECT COUNT(*) FROM users WHERE last_login < '2024-01-01';
SELECT * FROM users WHERE last_login < '2024-01-01' LIMIT 5;

-- 2. Show the user the proposed mutation, get explicit confirmation, then:
BEGIN;
DELETE FROM users WHERE last_login < '2024-01-01';
-- 3. Verify the row count matches the dry run
-- 4. COMMIT; or ROLLBACK;
```

For `DROP` and `ALTER`, run `EXPLAIN` or `\d table_name` (Postgres) / `DESCRIBE table_name`
(MySQL) / `.schema table_name` (SQLite) first and show the user the current shape.
