# GATE-04 — Idempotency + Concurrency

## Invariant

For one governed release request:

> **100 concurrent requests -> exactly 1 value movement.**

The PostgreSQL release path protects the operation with a unique idempotency key and row lock. The first committed operation becomes `COMPLETED`; later identical requests replay the completed result.

## Proof targets

- one non-replay result
- 99 replay results
- one release operation
- one witness
- one outbox event
- source balance moved exactly once
- destination balance moved exactly once
- same idempotency key with a different transaction conflicts

## Failure behavior

- same key + same payload -> replay
- same key + different payload -> idempotency conflict
- concurrent processing -> serialized by database row locking
- no second value movement

## Test requirement

Integration tests require `GERCHAIN_TEST_DATABASE_URL` and a real PostgreSQL database. Without that environment variable the tests skip; therefore a passing source test alone is not production proof.
