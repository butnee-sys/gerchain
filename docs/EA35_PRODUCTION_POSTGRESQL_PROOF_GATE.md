# EA-35.14 — Production PostgreSQL Proof Gate

Status: IN PROGRESS / NOT LOCKED  
Branch: feat/ea21-transaction-aware-ledger  
Reviewed runtime correction commit: e860f502f3e1a2d56fd873ad2faab7b1ab630740

## Evidence observed
- The combined GitHub commit status for the reviewed SHA contains Snyk security status `success`.
- This status does not prove migration execution, PostgreSQL boot, lifecycle correctness, recovery, or reconciliation.
- `postgres/schema/001_concurrency.sql` contains a `schema_version` table and canonical ledger/outbox/witness/idempotency tables, but this inspection does not establish that migration versions 1–16 are present, ordered, checksummed, or applied.
- `ProductionRuntimeFactory.initialize()` uses SQLAlchemy `metadata.create_all`; this is table creation, not a versioned migration runner and cannot by itself prove migration history 1–16.
- Production entrypoint/runtime wiring was corrected to instantiate `ProductionRuntimeFactory(ProductionRuntimeConfig(...)).create()` and configure Canonical Ledger authority. Actual PostgreSQL boot remains unverified.

## Required execution evidence
1. Identify the authoritative migration runner and enumerate migration versions 1–16.
2. On a disposable, clean PostgreSQL instance, run all migrations; capture exit status and logs.
3. Run the same migrations a second time; confirm idempotency and unchanged checksums/history.
4. Inspect actual PostgreSQL catalogs for required tables, columns, unique indexes, CHECK/FK constraints, constraint expressions, and `convalidated` state; fail if any required constraint is missing or `NOT VALID`.
5. Boot production entrypoint at the exact tested commit SHA against that database.
6. Exercise CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, replay, conflicting replay, and rollback.
7. Restart/recovery test, then run `deep_reconcile_value_truth(session)`; require zero issues.
8. Attach logs, SQL catalog report, migration history/checksums, commit SHA, and test summary to the release evidence.
9. Obtain independent re-performance before production lock.

## Hard gate
No result may be marked GREEN from static inspection alone. A failed, missing, or inaccessible execution result is NOT VERIFIED, not PASS. Do not claim production-ready or lock the architecture until all required evidence is tied to one commit SHA.
