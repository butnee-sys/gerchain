# EA-35 Deep Value Truth Contract

Status: IN PROGRESS / NOT LOCKED

## Purpose
The deep reconciliation gate proves that canonical value movement is structurally aligned with its escrow, witness, outbox, idempotency, and integrity evidence.

## Canonical value operations
- FUND
- RELEASE
- REFUND
- CANCEL
- SETTLEMENT

LOCK is state-only and must not require a ledger movement.

## Required graph
For each canonical value movement:
Movement -> Escrow aggregate
Movement -> Witness
Movement -> Outbox
Movement -> Durable Idempotency
Movement -> Integrity hash

The Outbox event must bind both aggregate_id and event_type to the canonical movement.

## Integrity
The movement integrity hash is derived from:
transaction_id, operation, escrow_id, source, destination, amount, currency.

A mismatch is a production evidence failure.

## Idempotency
Replay of the same operation is allowed.
Re-use of an idempotency key with a different request is a conflict.
State-only idempotency records must not be falsely classified as orphaned value movement evidence.

## Reconciliation invariant
Balance equality alone is insufficient:
Balance equality != Value-truth equality.

A production value operation is reconciled only when its complete evidence graph is consistent.

## Production gate
This contract is not a production lock. Fresh PostgreSQL execution, CI evidence, recovery verification, and independent re-performance are required before lock.
