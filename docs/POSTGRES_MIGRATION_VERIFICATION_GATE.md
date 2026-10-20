# PostgreSQL Migration Verification Gate

Status: IN PROGRESS / NOT LOCKED

Scope: canonical production persistence only. SHUUD is explicitly out of scope and must not be imported, invoked, or modified by these checks.

Every result must record the exact Git commit SHA, PostgreSQL server version, migration runner version, database isolation level, test command, exit code, and relevant database snapshots.

## M1 — Concurrent migration

Use two independent PostgreSQL connections/processes against the same disposable database and the same migration version. Synchronize both immediately before migration execution. Assert:
- exactly one schema_version row exists for the version;
- the migration's DDL is present exactly once;
- both callers return a defined success/idempotent outcome, or one safely waits and rechecks;
- no duplicate-object or swallowed checksum error is treated as success.

The migration runner must serialize version application with a PostgreSQL transaction-scoped advisory lock (or an equivalent proven serialization mechanism) and re-read schema_version after obtaining the lock. A primary key alone prevents duplicate rows but does not prove safe concurrent execution.

## M2 — Version uniqueness and checksum mismatch

Assert schema_version.version is protected by a PRIMARY KEY or UNIQUE constraint. Apply a version, then rerun with a deliberately changed checksum for that same version. The runner must fail closed with a checksum-mismatch error; it must not overwrite, ignore, or silently normalize the recorded checksum.

## M3 — Idempotent rerun

Capture ordered (version, checksum) rows after the first run. Rerun all migrations and capture them again. Assert exact equality of ordered rows and that no additional migration record or duplicate DDL effect appears.

## M4 — Atomic rollback

On a disposable PostgreSQL database, run a test migration that creates a marker object and then deliberately raises an error before recording completion. Assert after failure:
- marker DDL is absent;
- no schema_version row exists for the failed version;
- all prior committed migration versions remain unchanged.

This requires the migration DDL and version record to run in one transaction. Non-transactional DDL or statements that force transaction boundaries must be rejected or explicitly handled as a separate, documented migration class.

## M5 — Production boot and authority

Run the real production entrypoint against PostgreSQL with required configuration. Assert:
- process exits successfully from initialization and remains alive until stopped;
- runtime reports canonical ledger authority;
- PostgreSQL dialect is active;
- canonical Ledger metadata/tables exist;
- no legacy AtomicRelease/ReleaseAccount initialization is used as the authoritative production path;
- invalid or missing PostgreSQL configuration fails closed.

A successful process start alone is insufficient: inspect runtime authority and database objects from a separate connection.

## Evidence record

For each gate record:
- exact commit SHA;
- test/workflow run URL and ID;
- PostgreSQL version;
- command and exit code;
- assertion results;
- schema_version before/after snapshots;
- final verdict: PASS, FAIL, or UNVERIFIED.

Do not label a gate PASS without fresh evidence tied to the exact SHA. The existing schema_version primary key in postgres/schema/001_concurrency.sql is only a partial M2 safeguard; it does not by itself satisfy M1–M4.
