# EAI Production Lock — Migration Integrity Gate

Status: IN PROGRESS / NOT LOCKED

Scope: EAI production gate only. SHUUD and SANDBOX are excluded.

## Gate 2 — Migration integrity and concurrency

This gate may be marked GREEN only when all six evidence items below are attached to the same exact commit SHA:

1. Two concurrent PostgreSQL connections execute migration bootstrap successfully without duplicate publication, inconsistent state, or checksum conflict.
2. `schema_version` contains exactly one row for every version 1 through 17, with no missing or duplicate versions.
3. Each recorded checksum matches the migration source checksum or an explicitly documented, approved historical checksum.
4. A second migration run is a no-op: no new migration rows, no duplicate history, and no schema drift.
5. The production runtime boots against real PostgreSQL, restarts, and confirms it is using the canonical schema after restart.
6. PostgreSQL test logs and CI results identify the same exact commit SHA under test.

## Evidence rule

Source-code review is not runtime evidence. A green source scan, local SQLite test, or CI result from a different SHA cannot satisfy this gate. Missing evidence is NOT VERIFIED, not PASS.

## Current evidence assessment

- Migration runner source includes session-scoped advisory locking, unique version publication, checksum comparison, and conflict-safe publication. This is implementation evidence only.
- Real PostgreSQL concurrency result: NOT VERIFIED here.
- Exact 1–17 database row-count result: NOT VERIFIED here.
- Full checksum verification result on a live database: NOT VERIFIED here.
- Idempotent rerun result on a live database: NOT VERIFIED here.
- Production runtime boot + restart + canonical schema result on live PostgreSQL: NOT VERIFIED here.
- All required logs and CI bound to one exact SHA: NOT VERIFIED here.

## Final lock rule

Do not mark Gate 2 complete and do not issue PRODUCTION READY FINAL LOCK until all six items pass on the same SHA. The overall EAI production status remains IN PROGRESS / NOT LOCKED.
