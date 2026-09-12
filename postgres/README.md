# GerChain PostgreSQL concurrency hardening

This branch isolates PostgreSQL transaction semantics before they are wired into the existing SQLite-compatible application layer.

## Invariants

1. Escrow state transition, audit record and outbox event commit atomically.
2. Concurrent transitions on the same escrow serialize with `FOR UPDATE`.
3. Expected-state validation rejects stale transitions.
4. Schema migrations serialize with a PostgreSQL transaction-scoped advisory lock.
5. Outbox claims use `FOR UPDATE SKIP LOCKED`.
6. A PROCESSING lease expires and can be recovered by another worker.
7. Event consumers use `event_id` as an idempotency key.
8. A failed transaction leaves no partial state/audit/outbox write.

## Validation order

- two concurrent escrow transitions
- double-release attempt
- rollback after state/audit/outbox work
- two concurrent schema migrators
- migration checksum mismatch
- two concurrent outbox workers
- expired PROCESSING lease recovery
- duplicate event delivery
- crash-after-effect / retry simulation

The existing SQLite database layer is intentionally not modified by this branch. The PostgreSQL path must pass concurrency tests before becoming the production persistence path.
