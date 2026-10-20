# EA-35 PostgreSQL Re-performance Evidence — 2026-10-10

## Status

**IN PROGRESS / NOT LOCKED.** No production-green claim is made by this record.

## Failed execution inspected

- Repository: `butnee-sys/gerchain`
- Workflow: PostgreSQL Concurrency
- Run: [36542458201](https://github.com/butnee-sys/gerchain/actions/runs/36542458201)
- Run number: 1618; attempt: 43
- Failed run head SHA: `e860f502f3e1a2d56fd873ad2faab7b1ab630740`
- Job: `postgres-concurrency`, job ID `113464773986`
- Outcome: **FAILED** — 5 passed, 1 failed.
- Artifact inventory: no artifacts returned for this run.

## Exact failure from job log

```
postgres/tests/test_concurrency.py:175
    list(pool.map(lambda _: migrate(), range(2)))
postgres/tests/test_concurrency.py:172
    apply_migrations(conn, MIGRATION_DIR)
postgres/migrations.py:53
    conn.execute(...)
psycopg.errors.UniqueViolation:
duplicate key value violates unique constraint "schema_version_pkey"
DETAIL: Key (version)=(2) already exists.
```

Failed SQL:

```sql
INSERT INTO schema_version(version, checksum) VALUES (%s, %s)
```

Interpretation: concurrent migration publishers raced to record the same schema version. That execution did not prove migration publication concurrency safety.

## Current source reviewed after the failed run

- Branch: `feat/ea21-transaction-aware-ledger`
- Reviewed branch tip SHA at inspection: `e3c58a21797181e1b7ac76425229278cc5b63afe`
- `postgres/migrations.py` blob SHA: `eb2d53a1d0e7ca7a5ab1c21c2f256e5806a1b543`
- Current source includes session-scoped PostgreSQL advisory serialization, a schema-version uniqueness barrier, `INSERT ... ON CONFLICT (version) DO NOTHING`, and a post-publication checksum check.
- The current PostgreSQL concurrency test uses a fresh isolated database and two independent connections.

These are source-level observations only. They do **not** establish that the current branch passes PostgreSQL concurrency. A fresh run against the reviewed SHA is still required.

## Required next evidence

1. Fresh exact-SHA PostgreSQL concurrency run.
2. Inspect job steps and full logs; save the run artifact bundle if emitted.
3. Verify both independent migration runners succeed, exactly one row exists per version, versions are contiguous, checksums remain stable after rerun, and no unexpected schema state remains.
4. Record run ID, attempt, head SHA, job ID, artifact names, and final result here only after the execution completes.
5. Continue production migration, atomic Ledger/Escrow/Witness/Outbox transaction, rollback, restart/recovery, and replay/idempotency checks only with evidence tied to the tested commit SHA.

**Release rule:** missing run, missing logs, missing artifact, or an unverified exact-SHA result is not GREEN.
