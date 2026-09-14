# PostgreSQL Authoritative Runtime

## Runtime modes

GerChain has two explicit modes:

- `test-memory`: lightweight in-memory harness for unit tests and local behavior tests.
- `production-postgresql`: durable release authority for production value flow.

Production construction must use `ProductionRuntimeFactory` with a PostgreSQL engine and session factory.

## Production release path

```text
G-3 / DEE authorization
        ↓
GerchainRuntime.release()
        ↓
PostgreSQLReleaseAdapter
        ↓
PostgreSQLAtomicRelease
        ↓
ONE DATABASE COMMIT
```

The production path persists the governed value movement, escrow transition, witness and outbox event in one transaction. Idempotency is protected by the database unique key and row lock.

The in-memory ledger is not treated as production authority.

## Fail-closed rule

If production mode is not configured, a caller may use the memory runtime only as a test harness. Production deployment must not silently fall back to in-memory value movement.
