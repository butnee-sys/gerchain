# EA-35.13 — PostgreSQL Production Re-performance Evidence

Date: 2026-09-30
Branch: feat/ea21-transaction-aware-ledger

## Verified facts

1. Commit e860f502f3e1a2d56fd873ad2faab7b1ab630740 had exact-SHA GitHub Actions failures in PostgreSQL Concurrency and core-gates.
2. PostgreSQL Concurrency failure: test_migrations_are_serialized_and_checksum_is_stable failed with schema_version duplicate key version=2.
3. core-gates failure: services/gerchain.py at that historical commit contained a malformed literal-escape function body and failed collection with SyntaxError.
4. The current branch runtime source no longer contains that malformed function body.
5. ProductionRuntimeFactory now constructs ProductionRuntimeConfig, applies PostgreSQL migrations, enforces the canonical production schema guard, configures Canonical Ledger authority, and requires that authority before returning the runtime.
6. The migration runner now serializes concurrent migration runners with a PostgreSQL advisory session lock while retaining an atomic migration transaction.
7. Production entrypoint now uses the actual ProductionRuntimeFactory constructor/create contract.

## Current gate

STATUS: IN PROGRESS / NOT LOCKED

The historical PostgreSQL failure is now traced to the pre-repair migration runner: the failed run reported a duplicate `schema_version(version=2)`. The current migration runner contains transaction-scoped PostgreSQL advisory locking and idempotent `INSERT ... ON CONFLICT DO NOTHING` recording, so that historical failure is not treated as evidence against the repaired runner. A fresh exact-SHA workflow execution is still required; current PostgreSQL execution is NOT claimed as verified until that run completes.

## Release rule

Do not mark EA-35 GREEN or lock production until a fresh exact-SHA PostgreSQL run proves:
- migration serialization,
- canonical schema completeness,
- production factory boot,
- canonical Ledger authority,
- value movement and replay/idempotency,
- deep value-truth reconciliation,
- recovery/restart behavior,
- and independent re-performance.
