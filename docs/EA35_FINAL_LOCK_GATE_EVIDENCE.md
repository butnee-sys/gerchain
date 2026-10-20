# EA-35 — Final Production Lock Gate Evidence

Status: **IN PROGRESS / NOT LOCKED**
Scope: Canonical PostgreSQL production runtime + migration history + same-SHA core gates.
Branch: `feat/ea21-transaction-aware-ledger`

## Evidence reviewed

- `services/gerchain_runtime_factory.py` applies `postgres.migrations.apply_migrations`, then checks canonical tables, columns, uniqueness, CHECK constraints, and migration versions.
- The canonical migration registry declares an ordered 16-file chain (versions 1–16) in `postgres/migrations/__init__.py`.
- Production schema validation requires `schema_version.version = [1, 2, ..., 16]`, unique version keys, canonical constraints, and validated constraints.
- `tests/test_production_runtime_factory_postgres.py` checks a real PostgreSQL connection, canonical tables, 16 version rows, SHA-256 checksum formatting, and absence of legacy Release authority.
- `.github/workflows/core-gates.yml` configures PostgreSQL 16, the focused PostgreSQL runtime tests, the full repository test suite, and `scripts/audit_migration_inventory.py` with `REQUIRE_MIGRATION_HISTORY=1`.

## Current gate result

The GitHub combined status query for the latest identified merge commit returned an empty status list. This is **UNVERIFIED**, not PASS. No run/job result or artifact has been retrieved here that proves a complete, uncancelled `core-gates` run for the exact current branch HEAD.

## Required final-lock criteria

1. Retrieve a completed, non-cancelled `core-gates` run for the exact branch HEAD SHA.
2. Confirm every required job succeeded; no skipped required PostgreSQL or migration gate.
3. Retrieve `migration-inventory-<head_sha>` and verify canonical file inventory, versions 1–16, checksums, and applied PostgreSQL `schema_version` rows.
4. Confirm every required check has the same exact `head_sha`; reject stale results from earlier commits.
5. Re-perform production-entrypoint boot and canonical transaction/evidence reconciliation against PostgreSQL.
6. Record the evidence URLs, run ID, exact SHA, migration report, and independent re-performance result before declaring PRODUCTION READY or FINAL LOCK.

## Decision

**Do not declare PRODUCTION READY or FINAL LOCK until all criteria above have fresh, same-SHA evidence.** A clean migration file inventory or successful ORM table creation alone is not production evidence.
