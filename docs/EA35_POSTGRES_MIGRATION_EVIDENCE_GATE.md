# EA-35.14 — PostgreSQL Migration and Evidence Gate Audit

Audit date: 2026-10-19
Audited repository snapshot: `butnee-sys/gerchain@4fd6b3b18a552e9d8a5d217953685751ed6d250f`

Status: **BLOCKED — NOT VERIFIED / NOT LOCKED**

This document records repository-level evidence only. It does not claim a live PostgreSQL execution.

## 1. Current-commit CI evidence

- Combined commit status endpoint returned an empty status list for `4fd6b3b18a552e9d8a5d217953685751ed6d250f`.
- Commit-associated workflow lookup returned no workflow runs.
- Therefore Python syntax, full test suite, PostgreSQL integration, migration-race test, and Snyk status are **UNVERIFIED** for this exact SHA. An empty check list is not a pass.

## 2. Workflow coverage gap

`.github/workflows/ci.yml` currently runs a selected list of tests:
- `tests/test_shuud_command_layer.py`
- `tests/test_shuud_command_api.py`
- `tests/persistence/test_atomic_ledger_transaction_boundary.py`
- `tests/persistence/test_deep_value_reconciliation.py`
- `tests/services/test_gerchain_runtime_refund_canonical.py`
- `tests/services/test_gerchain_runtime_cancel_canonical.py`

The workflow does not declare a PostgreSQL service/container, does not show a live migration-race test, and does not run the full repository test suite. It therefore cannot establish the requested PostgreSQL production gate.

## 3. Migration-history and concurrency findings

The inspected migration files are:
- `postgres/schema/001_concurrency.sql`
- `postgres/schema/002_canonical_production.sql`
- `postgres/schema/003_ea22_canonical_escrow_lifecycle.sql`
- `postgres/schema/004_ea25_durable_idempotency.sql`
- `postgres/schema/005_ea26_value_flow_persistence.sql`

Findings requiring resolution before production lock:

1. `001_concurrency.sql` creates a `schema_version(version, checksum, applied_at)` table, but the inspected workflow does not invoke a migration runner or assert a complete ordered/checksummed migration history.
2. Migrations 002–005 overlap in their definitions of canonical ledger, witness, outbox, idempotency, and escrow lifecycle schema. `CREATE TABLE IF NOT EXISTS` does not reconcile an already-existing table's columns, types, constraints, or indexes.
3. Migration 002 uses DDL and a data backfill without an explicit encompassing `BEGIN/COMMIT` block. Its atomicity and rerun behavior must be demonstrated against the supported PostgreSQL version.
4. Migration 002 defines ledger balances and movement amounts as `BIGINT`; migration 005 defines them as `INTEGER`. Whichever migration runs first can determine the actual column type because subsequent `CREATE TABLE IF NOT EXISTS` does not alter it.
5. Migrations 002 and 003 both modify the escrow lifecycle schema. Concurrent execution can race on constraint replacement and DDL unless a serialized migration lock is enforced.
6. The current workflow provides no evidence of two concurrent migration runners, interrupted migration recovery, checksum drift detection, or a post-migration schema contract check.

These are static review findings, not proof that a live database currently fails. A real PostgreSQL run is required to establish runtime behavior.

## 4. Required gate sequence

1. Add or identify one authoritative, serialized migration runner with ordered versions and immutable checksums. Do not treat ORM `metadata.create_all` as a substitute for migrations.
2. Resolve overlapping migrations and the `INTEGER`/ `BIGINT` type conflict; define supported upgrade paths from both an empty database and each supported prior schema.
3. Add a PostgreSQL-backed CI job that:
   - waits for PostgreSQL readiness;
   - runs Python compile/syntax checks;
   - applies migrations from an empty database;
   - runs two migration invocations concurrently and asserts one coherent migration history;
   - reruns migrations and asserts idempotent no-op behavior;
   - verifies schema columns, types, constraints, indexes, and checksums;
   - runs the full test suite plus canonical value-flow and deep-reconciliation tests;
   - captures the exact commit SHA, database version, migration history, test exit status, and logs.
4. On the same database and same commit, execute the canonical value-flow graph audit: Ledger movement ↔ Escrow ↔ Witness ↔ Outbox ↔ Idempotency ↔ integrity hash.
5. Record Snyk and all required CI checks for the exact same commit. A missing, pending, or empty result remains UNVERIFIED.
6. Only after all evidence passes, issue a separate production-lock decision. Until then the overall status remains **IN PROGRESS / NOT LOCKED**.

## 5. Production-lock invariant

No production readiness claim may be made from source inspection alone. The final evidence bundle must bind each result to the exact commit SHA and include live PostgreSQL execution evidence.
