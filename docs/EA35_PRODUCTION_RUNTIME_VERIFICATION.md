# EA-35.13 Production Runtime Construction Verification

Status: IN PROGRESS / NOT LOCKED

Verified against branch `feat/ea21-transaction-aware-ledger`.

## Verified

1. `production_entrypoint.py` now constructs `ProductionRuntimeConfig` and instantiates `ProductionRuntimeFactory`.
2. `ProductionRuntimeFactory` requires a PostgreSQL URL and a PostgreSQL SQLAlchemy engine.
3. The factory creates canonical persistence metadata for Ledger, Escrow, Outbox, Durable Idempotency, and Transaction Witness.
4. The factory configures `GerchainRuntime.configure_canonical_ledger()` and calls `require_canonical_ledger_authority()`.
5. The entrypoint additionally asserts `runtime.is_canonical_ledger_authoritative`.
6. The previous invalid class-level `ProductionRuntimeFactory.create(...)` call has been removed.
7. Legacy PostgreSQL Release authority is no longer used by the production factory construction path.

## Evidence

Correction commit: `e860f502f3e1a2d56fd873ad2faab7b1ab630740`.

The production entrypoint therefore has source-level constructor/authority consistency.

## Blocking production evidence

This does NOT prove a real PostgreSQL boot.

The current legacy SQL file `postgres/schema/001_concurrency.sql` defines `escrows` with only CREATED/LOCKED/RELEASED and does not define the canonical GerChain tables `gerchain_ledger_accounts`, `gerchain_ledger_movements`, `gerchain_outbox_events`, `gerchain_idempotency_records`, or `gerchain_transaction_witnesses`.

SQLAlchemy `metadata.create_all()` does not alter an already-existing `escrows` table. Therefore an existing database created from the legacy schema cannot be considered migration-complete merely because the factory boots.

Required next gate:

POSTGRESQL MIGRATION -> REAL BOOT -> LIFECYCLE RE-PERFORMANCE -> DEEP VALUE-TRUTH RECONCILIATION -> RECOVERY -> EXACT-SHA CI EVIDENCE -> INDEPENDENT RE-PERFORMANCE.

No GREEN or production lock is declared until those gates produce fresh evidence.
