# GATE-05 — Crash / Recovery Contract

## Invariants

1. Governance failure happens before any database mutation.
2. A database failure before commit rolls back value movement, witness, outbox, and idempotency completion together.
3. A committed release is replayable when the response is lost.
4. Replay never performs a second value movement.
5. Outbox delivery is at-least-once; event consumers must therefore be idempotent.
6. An expired PROCESSING outbox lease returns to PENDING and may be claimed again.
7. Recovery must never create a second authoritative value movement.

## Release state model

```text
REQUEST
  -> PROCESSING
  -> COMMITTED / COMPLETED

PROCESSING + transaction rollback -> no authoritative mutation
COMPLETED + response loss -> REPLAY
OUTBOX PROCESSING + lease expiry -> PENDING -> PROCESSING
```

The authoritative value transaction remains the PostgreSQL atomic release. The outbox is a durable delivery mechanism, not a second ledger.

## Verification

`tests/test_release_crash_recovery_contract.py` verifies post-commit replay and expired outbox recovery against `GERCHAIN_TEST_DATABASE_URL`.
