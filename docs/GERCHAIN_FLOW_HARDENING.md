# GerChain Flow Hardening

## Protected mutation path

```text
Request
  -> Idempotency
  -> Limit
  -> Hold
  -> Transaction Lifecycle
  -> G-3 / DEE Authorization
  -> Escrow
  -> Atomic Settlement
  -> Ledger + Witness
  -> FINAL
```

## Invariants

1. The same idempotency key and materially identical request return the original result.
2. Reusing an idempotency key for a different request is denied.
3. Hold reserves capacity but does not move value.
4. Limit checks constrain permitted exposure but do not move value.
5. Authorization remains DEE-owned; no second authorization engine is introduced.
6. Escrow remains the operational escrow boundary; no second escrow engine is introduced.
7. Ledger remains the authoritative value record; no second ledger is introduced.
8. Witness remains the evidence chain for executed value movement.
9. Failed settlement restores ledger, escrow, record and witness checkpoints.
10. Terminal transaction state is FINAL and cannot transition further.

## Concurrency target

The in-memory idempotency capability is a correctness layer for one runtime.
Production PostgreSQL enforcement must additionally use a unique idempotency key,
transactional row locking, atomic state transition and commit. A process-local
Python lock is not sufficient for concurrent workers.
