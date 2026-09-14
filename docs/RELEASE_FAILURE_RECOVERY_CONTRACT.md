# GerChain Release Failure & Recovery Contract

## Invariant

A release is authoritative only when governance passes and the database transaction commits.

```text
Decision APPROVE
+ Authorization AUTHORIZED
+ Trust PASS
+ Transparency PASS
+ Performance PASS
+ Evidence VERIFIED
        |
        v
Ledger + Escrow + Witness + Outbox + Idempotency
        |
        v
ONE DATABASE COMMIT
```

## Pre-mutation failure

If governance fails, no authoritative mutation is permitted:

- ledger unchanged
- escrow remains LOCKED
- no witness
- no outbox event
- no completed release operation

## Transaction failure

If any database operation fails before commit, the transaction must roll back as one unit. No partial ledger, escrow, witness, outbox, or idempotency completion may survive.

## Post-commit response loss

If the commit succeeds but the client loses the response, a retry with the same idempotency key and equivalent request must return `replay=true`. It must not move value again.

## Outbox recovery

Outbox delivery is separate from authoritative value mutation. An event may move:

```text
PENDING -> PROCESSING + lease -> COMPLETED
                         |
                    lease expires
                         v
                       PENDING
```

The outbox event has a unique `event_id`. Recovery may retry delivery, but must never perform a second authoritative value movement.

## Exactly-once boundary

Exactly-once value movement is guaranteed by the database release transaction and unique transaction/idempotency constraints. External event delivery is at-least-once and therefore consumers must be idempotent.

## Test status

The repository contains PostgreSQL integration contracts for governance rejection, post-commit replay, outbox recovery, and concurrency. These tests require `GERCHAIN_TEST_DATABASE_URL`; repository writes alone do not constitute execution against a live PostgreSQL instance.
