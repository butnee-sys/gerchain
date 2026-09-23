# EA-35.13 — PostgreSQL Production Proof Gate

Status: IN PROGRESS / NOT LOCKED

## Scope

This gate verifies that the production construction path uses PostgreSQL and the Canonical Ledger rather than the legacy in-memory or ReleaseAccount value authority.

## Implemented controls

1. `ProductionRuntimeFactory` requires a PostgreSQL URL and PostgreSQL engine.
2. The factory applies `postgres/schema` migrations before constructing the runtime.
3. The runtime is configured through `configure_canonical_ledger()`.
4. `require_canonical_ledger_authority()` is enforced during construction.
5. Canonical persistence includes:
   - `gerchain_ledger_accounts`
   - `gerchain_ledger_movements`
   - `escrows`
   - `gerchain_transaction_witnesses`
   - `gerchain_outbox_events`
   - `gerchain_idempotency_records`
6. A real-PostgreSQL integration test covers:
   - factory construction;
   - Canonical Ledger authority assertion;
   - account initialization;
   - FUND;
   - LOCK;
   - RELEASE;
   - durable balance persistence;
   - escrow terminal state;
   - deep value-truth reconciliation.
7. A GitHub Actions PostgreSQL service workflow is present at
   `.github/workflows/production-postgres-proof.yml`.

## Evidence boundary

The repository currently contains the proof test and CI gate, but the GitHub connector returned no workflow run for the latest synchronization commits. Therefore this document does **not** classify the PostgreSQL runtime gate as GREEN.

The required evidence for closure is a completed GitHub Actions PostgreSQL job for the exact branch SHA, with the integration test passing.

## Lock rule

No production lock is declared until the real PostgreSQL job is observed as successful and the exact-SHA evidence is recorded.
