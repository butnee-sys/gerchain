# EA-35 Migration Authority Audit

Status: **IN PROGRESS / NOT LOCKED**
Scope: repository migration entrypoints, canonical SQL selection, historical checksums, and workflow evidence. This document is not a substitute for inspecting a real deployment's `schema_version` rows.

## 1. Runtime import resolution

Python resolves `import postgres.migrations` to the package `postgres/migrations/__init__.py`, not the same-name sibling module `postgres/migrations.py`, because the package directory exists.

Evidence on the reviewed branch:
- Active package: `postgres/migrations/__init__.py`, Git blob `8d9eb7720a1ada2a9c45fd79943c4763d30f436b`.
- Shadowed sibling module: `postgres/migrations.py`, Git blob `1fb7492a628fcc7e089abe453d5521d3a811482d`.
- Package exposes the frozen 17-name `_CANONICAL_FILES` manifest and strict contiguous-version selector.
- `postgres/migration_runner.py` re-exports the package implementation.
- `scripts/postgres_migration_runner.py` selects only files inside `postgres/migrations/` and calls the package's `apply_migrations`.

Therefore the package implementation is the effective canonical runner for normal imports. The sibling module is a duplicate-looking source file but is not the implementation imported by these normal call paths. It is retained pending a separate history/consumer audit; do not delete it solely from this finding.

## 2. Competing legacy entrypoint

Previously, `scripts/apply_postgres_migration.py` independently executed `postgres/schema/001_concurrency.sql`, wrote version 1 using a separate advisory-lock key, and therefore created a second migration publication path.

That path has now been changed to delegate to `scripts.postgres_migration_runner`. Standalone execution from `postgres/schema/` fails closed. SQLAlchemy-style PostgreSQL URLs are normalized before calling psycopg.

Relevant migration sources:
- Canonical ordered chain: `postgres/migrations/001_canonical_production.sql` through `017_ea35_created_witness_event.sql`.
- Legacy schema directory contains competing files including `postgres/schema/001_concurrency.sql` and multiple version-002/003/005/006/008/009 files.
- The historical source `postgres/schema/001_concurrency.sql` has a recorded legacy checksum in `LEGACY_CHECKSUMS[1]`: `6eea24dae8b3ac9aa9413a32da1617250f14725bdb19f50e5d8300308ad173d4`. The canonical runner accepts recorded historical checksums without rewriting history.

Git blob SHAs identify repository content; they are not the SQL SHA-256 migration checksums. The runner calculates SHA-256 from the exact SQL bytes.

## 3. Canonical manifest

The package manifest is an explicit, contiguous sequence of versions 1–17. A new PostgreSQL-gate test now asserts that the selected physical filenames match the manifest and that the legacy schema runner rejects a standalone schema file. The canonical migration workflow runs this test before the fresh-database migration scenarios.

## 4. What repository evidence cannot prove

No live production database connection or exported production `schema_version` table was available in this audit. Consequently, this audit cannot claim which exact migration versions/checksums are already applied in a deployed database. That determination requires a read-only capture of:
```sql
SELECT version, checksum, applied_at
FROM schema_version
ORDER BY version;
```
The capture must be compared with the canonical manifest and `FROZEN_CHECKSUMS`/`LEGACY_CHECKSUMS`, without silently rewriting conflicting history.

## 5. Release gates still required

1. Fresh PostgreSQL 16 migration run from an empty schema.
2. Exact contiguous history 1–17, one row per version, checksum-accepted for every row.
3. Schema/catalog assertions for required canonical tables, columns, constraints, and indexes.
4. Upgrade/replay/checksum-mismatch/concurrent-runner tests.
5. Exact-SHA CI completion; queued or absent checks are **UNVERIFIED**.
6. Workflow overlap inventory and consolidation decision after migration evidence completes.
7. Independent re-performance and explicit production-lock approval.

Until all required gates pass on one exact commit SHA, status remains **IN PROGRESS / NOT LOCKED**. PR #100 must not be merged as part of this audit.
