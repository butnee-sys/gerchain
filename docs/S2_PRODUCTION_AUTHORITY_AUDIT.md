# S2 Production Authority and Transaction-Boundary Audit

Status: **IN PROGRESS / NOT LOCKED**
Branch inspected: `feat/ea21-transaction-aware-ledger`
Scope: S2-01 through S2-04 source-level audit. This document is not a CI result or a PostgreSQL re-performance attestation.

## S2-01 — Legacy value authorities

Inspected:
- `persistence/atomic_release.py`
- `persistence/atomic_settlement.py`
- `services/gerchain_runtime.py`
- `services/gerchain_runtime_factory.py`

Findings:
- `ReleaseAccount`, `ReleaseEscrow`, and `ReleaseWitness` remain mapped in `persistence/atomic_release.py`; the module still contains its own commit-capable release implementation. Their existence is not proof they are production-authoritative, but it is a residual legacy path that must be explicitly proven unreachable from production entrypoints and all API/runtime callers.
- `AccountBalance` and `SettlementMovement` remain mapped in `persistence/atomic_settlement.py`; legacy code retains its own session/commit path. This is a duplicate value-authority risk if any production caller still reaches it.
- `GerchainRuntime` still imports/constructs `MoneyLedger` for the test-memory harness. Production safety depends on every value-mutating and balance-reading method failing closed when Canonical Ledger authority is not attached; this requires method-by-method tests, not only constructor checks.
- Source-level inspection alone cannot establish that no external import/caller or deployment configuration invokes legacy modules.

Required closure evidence:
1. repository-wide call graph/search on the exact candidate commit, including API routes, web UI, CLI, workers and tests;
2. regression tests proving production-mode legacy paths fail closed and never mutate legacy tables;
3. PostgreSQL integration evidence that only `gerchain_ledger_accounts` and `gerchain_ledger_movements` are authoritative.

## S2-02 — Escrow creation/read/mutation

Inspected:
- `persistence/escrow_aggregate.py`
- `services/gerchain_runtime.py`
- `production_entrypoint.py`

The canonical aggregate model `CanonicalEscrow` is mapped to `escrows` and defines CREATED/FUNDED/LOCKED/RELEASED/REFUNDED/CANCELLED transitions. The runtime has durable read paths and canonical operation branches, but this audit has not yet proven every write entrypoint is routed through the aggregate boundary. Direct ORM/SQL writes to `escrows`, legacy SQLite escrow routes, and alternate runtime paths must be enumerated and tested fail-closed.

Required closure evidence:
- complete caller map for every INSERT/UPDATE/DELETE against `escrows`;
- test that unauthorized/direct legacy mutation endpoints cannot change canonical state;
- PostgreSQL lifecycle test across all allowed transitions and terminal-state rejection.

## S2-03 — Outbox / witness / idempotency transaction boundary

Inspected:
- `persistence/transactional_outbox.py`
- `persistence/recovery_outbox.py`
- `persistence/atomic_value_transaction.py`

`enqueue_in_transaction(session, ...)` explicitly uses the caller's session and does not commit. The legacy `PostgreSQLOutbox` implementation has independent session/commit behavior for event delivery and must not be used to enqueue the intent for a canonical value movement. Canonical value-movement closure requires Ledger movement, escrow transition, witness, durable idempotency completion, and outbox intent to commit or roll back together.

Required closure evidence:
- call-site audit proving all canonical movement paths use `enqueue_in_transaction` through `AtomicValueTransaction`;
- injected-failure tests at each stage proving zero partial committed evidence;
- post-commit delivery/recovery test proving the dispatcher cannot create a second value movement.

## S2-04 — Production-to-memory fallback

The runtime retains an in-memory harness by design. That is acceptable only for explicit test mode. The source audit found multiple Canonical Ledger branches and legacy memory dependencies; each public operation must be tested with production mode selected but canonical authority absent, and must raise/deny rather than fall back.

Required operation matrix:
- CREATE escrow
- FUND
- LOCK
- RELEASE
- REFUND
- CANCEL
- SETTLEMENT
- GET balance
- CREATE account
- GET escrow state

For each operation assert: no memory balance mutation, no legacy-table mutation, no canonical partial write, and fail-closed error.

## Verification gate

Not yet evidenced in this audit:
- exact-SHA CI result;
- real PostgreSQL clean-database migration and boot;
- full lifecycle and deep value-truth reconciliation against PostgreSQL;
- restart/recovery re-performance;
- independent re-performance.

**Decision: S2 remains OPEN. No production-ready or GREEN claim is authorized by this document.**
