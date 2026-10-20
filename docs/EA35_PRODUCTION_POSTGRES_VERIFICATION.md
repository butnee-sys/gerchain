# EA-35 Production PostgreSQL Verification

Status: IN PROGRESS / NOT LOCKED

## Scope

This evidence contract verifies that the production GerChain runtime uses PostgreSQL Canonical Ledger authority and that value-truth evidence remains internally consistent.

## Production boot invariants

ProductionRuntimeFactory must:

1. Reject non-PostgreSQL database URLs.
2. Apply the authoritative PostgreSQL migration set.
3. Require schema_version >= 12.
4. Require the canonical tables:
   - schema_version
   - escrows
   - gerchain_ledger_accounts
   - gerchain_ledger_movements
   - gerchain_transaction_witnesses
   - gerchain_outbox_events
   - gerchain_idempotency_records
5. Construct GerchainRuntime with configure_canonical_ledger().
6. Establish is_canonical_ledger_authoritative == true.
7. Not configure the legacy PostgreSQL ReleaseAccount authority.

## PostgreSQL verification workflow

Workflow:
.github/workflows/production-postgres.yml

The workflow provisions PostgreSQL 16 and runs:

- tests/integration/test_production_postgres_boot.py
- tests/integration/test_postgresql_production_gate.py
- tests/persistence/test_deep_value_reconciliation.py

## Value-flow proof target

The integration gate covers:

- Canonical production boot
- schema migration history
- account creation
- settlement and replay
- FUND
- LOCK
- RELEASE
- REFUND
- CANCEL
- canonical balance reads
- deep value-truth reconciliation
- witness count
- outbox count
- canonical movement count

## Current evidence status

Repository implementation evidence: PRESENT.

Workflow definition evidence: PRESENT.

Fresh successful GitHub Actions execution for the current production-runtime commit: NOT YET VERIFIED through the available commit-run evidence endpoint.

Therefore this document does not declare GREEN or PRODUCTION LOCK.

## Lock condition

EA-35 may move to LOCKED only after a fresh exact-SHA PostgreSQL workflow execution succeeds and its evidence confirms the complete production value-flow and deep reconciliation gates.

## Hard invariant

No production value movement may bypass the Canonical Ledger mutation boundary.

No legacy ReleaseAccount, MoneyLedger, AccountBalance, SQLite value store, or application-owned balance mutation may become authoritative.
