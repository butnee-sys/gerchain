# EA-35 Production Re-performance Status

Status: IN PROGRESS / NOT LOCKED

## Verified repository facts

- Production entrypoint requires a PostgreSQL `GERCHAIN_DATABASE_URL`.
- Production runtime construction uses `ProductionRuntimeFactory.create(...)`.
- The factory applies versioned PostgreSQL migrations from `postgres/schema`.
- The factory configures `GerchainRuntime` with `configure_canonical_ledger()`.
- Production boot fails closed if canonical persistence tables/columns are missing.
- Production boot validates the canonical escrow state constraint.
- Canonical value authority remains `gerchain_ledger_accounts` and `gerchain_ledger_movements`.
- Legacy ReleaseAccount/AtomicRelease is not used as the production authority by the current factory.

## Current migration evidence

Migration `002_canonical_production.sql` creates the canonical ledger, witness, idempotency and transactional outbox stores and extends the legacy escrow table with production fields and lifecycle states.

Migration application is serialized by a PostgreSQL advisory transaction lock and protected by `schema_version` checksums.

## Runtime verification boundary

Repository inspection confirms the construction path is internally consistent:

GERCHAIN_DATABASE_URL
-> SQLAlchemy PostgreSQL engine
-> versioned migrations
-> canonical schema validation
-> GerchainRuntime
-> Canonical Ledger authority

However, no fresh executed PostgreSQL workflow result is currently available for the exact branch tip. Therefore this evidence is not an execution-level GREEN claim.

## Release gate

The following remain required before production lock:

1. Fresh PostgreSQL execution against the exact branch tip.
2. CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ execution evidence.
3. Deep value-truth reconciliation after the transaction matrix.
4. Restart/recovery evidence with no duplicate value movement.
5. Exact-SHA CI evidence.
6. Independent re-performance.

No production lock is declared until all release gates have evidence.
