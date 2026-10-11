# EA-35 CI Re-performance Evidence

Status: IN PROGRESS / NOT LOCKED

## Evidence captured

- Commit under inspection: `e860f502f3e1a2d56fd873ad2faab7b1ab630740`
- PostgreSQL Concurrency workflow run: [36542458201](https://github.com/butnee-sys/gerchain/actions/runs/36542458201)
- Job: `postgres-concurrency` (job ID `113464773986`)
- Result: **FAILURE** — 5 passed, 1 failed.
- Failing test: `postgres/tests/test_concurrency.py::test_migrations_are_serialized_and_checksum_is_stable`
- Observed PostgreSQL error: `UniqueViolation: duplicate key value violates unique constraint "schema_version_pkey"; Key (version)=(2) already exists.`

This is a real failure, not a green result. It means the migration concurrency proof did not pass for the inspected commit.

## Current-code observation

The current branch version of `postgres/migrations/__init__.py` uses a transaction-scoped advisory lock and publishes version rows with `INSERT ... ON CONFLICT (version) DO NOTHING`, followed by a checksum verification. This appears intended to address duplicate publication, but **the current branch's exact commit has not yet been shown by a successful fresh PostgreSQL run**. The failed run above predates proof of that correction and must not be treated as proof that the current version passes.

## Required re-performance

1. Run the PostgreSQL concurrency test against the exact current branch commit using a truly fresh isolated database.
2. Verify two distinct backend PIDs, one row for each migration version 1–13, stable checksums after rerun, and no duplicate version publication.
3. Run the canonical production schema initialization against PostgreSQL and verify all required tables and columns.
4. Exercise atomic value movement, rollback, idempotent replay/conflict, witness/outbox integrity, and restart/recovery on PostgreSQL.
5. Attach the exact commit SHA and successful workflow run to this evidence file before changing any gate to GREEN.

## Decision

No production lock. The PostgreSQL migration concurrency gate remains **RED / UNVERIFIED** until fresh evidence passes on the exact current commit. A successful Snyk status does not substitute for PostgreSQL integration evidence.
