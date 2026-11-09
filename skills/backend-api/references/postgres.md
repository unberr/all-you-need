# PostgreSQL patterns

- **Types:** `timestamptz` for instants, `numeric` for money (or integer minor units), `uuid` or `bigint` identity for keys, `text` over `varchar(n)` unless a limit is a rule, `jsonb` for genuinely schemaless data with a GIN index where you query inside it.
- **Constraints:** primary key on every table, foreign keys with a chosen `ON DELETE`, `NOT NULL` by default, `CHECK` for invariants, `UNIQUE` for natural keys. The database is the last line of defense against bad data.
- **Indexes:** index foreign keys and the columns in `WHERE`, `JOIN` and `ORDER BY`; composite indexes ordered by equality columns first, then range; partial indexes for hot subsets; covering indexes (`INCLUDE`) to avoid heap fetches; check usage with `pg_stat_user_indexes`. `CREATE INDEX CONCURRENTLY` on live tables.
- **Plans:** `EXPLAIN (ANALYZE, BUFFERS)` on slow queries; look for sequential scans on large tables, row-estimate mismatches (run `ANALYZE`), sorts spilling to disk, nested loops over big sets.
- **Pagination:** keyset (`WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT n`) over `OFFSET` for large tables.
- **Concurrency:** `SELECT ... FOR UPDATE` (with `SKIP LOCKED` for queues), advisory locks for application-level mutual exclusion, `INSERT ... ON CONFLICT` for upserts, serializable isolation with retry for complex invariants. Keep transactions short; set `lock_timeout` and `statement_timeout`.
- **Row-level security** for multi-tenant isolation: policies on each tenant table, set the tenant in a session setting, and test that a different tenant sees nothing.
- **Migrations:** add nullable columns or defaults (fast on modern versions), backfill in batches, then add `NOT NULL` via a validated `CHECK` constraint; add foreign keys `NOT VALID` then `VALIDATE CONSTRAINT`; never rewrite a big table in a transaction during peak load.
- **Connections:** use a pool (PgBouncer or the driver's), size it to cores and database limits, one pool per process, close idle connections, use prepared statements with the pooler's mode in mind.
- **Operations:** autovacuum tuned for hot tables, monitor bloat and replication lag, backups with tested restores (`pg_dump` for logical, base backups and WAL for point-in-time recovery), least-privilege roles (application role without `CREATE`, migration role separate).
