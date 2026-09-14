# PostgreSQL Atomic Release

## Purpose

`PostgreSQLAtomicRelease` is a persistence transaction boundary. It does not create a second Ledger, Escrow, Witness, or Authorization engine.

## Atomic boundary

```text
BEGIN
  Idempotency lock
  Escrow row lock
  Source/Destination account locks
  Balance validation
  Ledger movement
  Escrow -> RELEASED
  Witness -> RELEASED
  Idempotency -> COMPLETED
COMMIT
```

Any exception before commit rolls back all database mutations.

## Exactly-once invariant

For one `(idempotency_key, transaction_id)` under concurrent requests:

- exactly one request may perform the value movement;
- exactly one escrow transition may occur;
- exactly one witness row may be created;
- exactly one idempotency operation row may exist;
- later identical requests replay the completed result;
- materially different requests using the same key are denied.

The integration test uses 100 concurrent PostgreSQL workers to exercise this invariant.

## Production requirement

The database must be the concurrency authority. Process-local Python locks are not sufficient. PostgreSQL row locks and unique constraints protect the mutation boundary across workers/processes.

The next hardening step is crash recovery for `PROCESSING` operations and a durable outbox event tied to the same commit.
