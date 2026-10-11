# EA-35 PostgreSQL Migration Inventory and Re-performance Gate

Status: IN PROGRESS / NOT LOCKED  
Purpose: record the exact migration runner and canonical migration selection from the repository. This document is an inventory, not proof that migrations passed on PostgreSQL.

## Single runner

- Canonical implementation: `postgres/migrations.py`
- Compatibility import only: `postgres/migration_runner.py`
- Public entrypoint: `apply_migrations(conn, migration_dir)`
- Migration manifest table: `schema_version`
- Serialization: PostgreSQL session advisory lock, key `73546501`, plus a table lock while reading/publishing version rows.
- Migration publication must be conflict-safe and checksum validation must fail closed.

## Canonical numeric migration sequence

The runner's explicit preferred-name map selects exactly these 13 SQL files on a fresh database:

1. `001_canonical_production.sql`
2. `002_canonical_production.sql`
3. `003_canonical_compatibility.sql`
4. `004_canonical_value_truth.sql`
5. `005_canonical_production.sql`
6. `006_canonical_movement_integrity.sql`
7. `007_canonical_production_reconciliation.sql`
8. `008_ea35_idempotency_compat.sql`
9. `009_canonical_movement_integrity_hardening.sql`
10. `010_canonical_evidence_constraints.sql`
11. `011_ea35_canonical_schema_finalization.sql`
12. `012_canonical_production.sql`
13. `013_ea35_canonical_schema_hardening.sql`

The repository also contains historical same-version SQL aliases. They are not all independently applied by the canonical runner. Existing installations may have checksums from documented historical aliases; the runner's frozen/legacy checksum maps determine whether those recorded versions are accepted. Do not rename, delete, or re-number these files without an explicit migration-history change and compatibility test.

## Required PostgreSQL re-performance gates

A single commit SHA must be tested against a real PostgreSQL service. The canonical workflow is `.github/workflows/canonical-postgres-gate.yml`.

1. **Migration integrity:** fresh install, already-applied migration replay, checksum mismatch fail-closed, and one publication per version under concurrent runners.
2. **Runtime boot:** factory/entrypoint must create a runtime with canonical Ledger authority; required canonical tables must exist after the supported migration path.
3. **Escrow lifecycle:** CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ exercise against PostgreSQL, with no alternate production value authority.
4. **Deep value truth:** movement, escrow, witness, outbox, idempotency, and integrity bindings reconcile; rollback and replay do not duplicate value movement.
5. **Concurrency and recovery:** concurrent migration publication and value-flow tests pass; failure/rollback/restart must not create partial state or duplicate movement.

## Evidence and lock rule

The workflow artifact must include the exact commit SHA, migration file hashes, workflow run ID/attempt, and per-gate logs. Record each gate's actual result; absence of a check is UNVERIFIED, not PASS. If any balance changes unexpectedly, checksum mismatch is not rejected, publication duplicates, or concurrency/recovery test fails, production remains HOLD and is not locked.

This inventory does not assert that the five gates have passed. The only valid lock decision is based on fresh successful evidence for one exact commit SHA and independent re-performance.
