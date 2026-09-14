# PostgreSQL Idempotency and Concurrency

GerChain's in-memory idempotency capability is retained for deterministic unit-level protection. Production mutation boundaries must use PostgreSQL as the cross-worker coordination point.

## Required invariant

```text
same operation + same idempotency key
        ↓
PostgreSQL unique constraint
        ↓
one authoritative mutation owner
        ↓
atomic value movement
        ↓
COMPLETED result persisted
        ↓
all later requests replay the result
```

## Conflict invariant

A reused key with a different request fingerprint is denied. It must never become a second transaction.

## Concurrency invariant

The database boundary uses `SELECT ... FOR UPDATE` for existing rows and a unique `(operation, idempotency_key)` constraint. The remaining production step is to bind the idempotency row lifecycle and the actual Ledger/Escrow mutation into the **same PostgreSQL transaction**. Committing the idempotency row separately from the value movement is not sufficient for exactly-once semantics.

## Failure invariant

If the value mutation rolls back, the idempotency operation must not remain permanently `COMPLETED`. A recovery/lease policy is required for abandoned `PROCESSING` rows.

## No process-local lock

A Python mutex is not the concurrency authority. PostgreSQL transaction isolation, row locking, unique constraints and atomic state transitions are the authority across workers and processes.
