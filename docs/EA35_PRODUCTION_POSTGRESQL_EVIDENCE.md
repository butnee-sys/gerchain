# EA-35 Production PostgreSQL Evidence

Status: VERIFIED AT BRANCH TIP — NOT A PRODUCTION LOCK

## Verified commit
- Branch: `feat/ea21-transaction-aware-ledger`
- Commit: `6fe9acfa1997b01b8e226cd49082dd59e2c2d7b7`
- Evidence date: 2026-09-29

## PostgreSQL evidence

The following GitHub Actions runs were completed successfully against the exact commit above:

| Evidence | Run | Result |
|---|---:|---|
| Production PostgreSQL verification | 36564420356 | SUCCESS |
| PostgreSQL production re-performance | 36564420322 | SUCCESS |
| Production PostgreSQL E2E | 36564420445 | SUCCESS |
| production-postgresql | 36564420327 | SUCCESS |
| production-postgres-gate | 36564420368 | SUCCESS |

### Detailed verification
Run 36564420356 job `postgres-production` executed:
1. `tests/integration/test_real_postgresql_production.py` — 1 passed.
2. `tests/integration/test_production_postgresql_value_flow.py tests/integration/test_production_postgres_flow.py` — 2 passed.
3. `tests/persistence/test_deep_value_reconciliation.py` — 19 passed.
4. PostgreSQL 16 service container was started and accepted connections.

The real PostgreSQL lifecycle test verifies:
- canonical production schema migration and schema guard;
- production runtime construction;
- Canonical Ledger authority;
- FUND → LOCK → RELEASE;
- REFUND;
- CANCEL;
- SETTLEMENT;
- final balances;
- final escrow states;
- deep value-truth reconciliation;
- second runtime construction after the first execution.

The production value-flow test verifies canonical PostgreSQL FUND/LOCK/RELEASE and deep reconciliation.

## Production entrypoint
Run 36564420327 completed successfully with:
- Production PostgreSQL boot;
- PostgreSQL value-flow integration and re-performance;
- production entrypoint syntax verification.

## Schema
Canonical PostgreSQL migrations currently extend through migration 010:
- 001 concurrency baseline
- 002 canonical production
- 003 canonical value authority
- 004 canonical value truth
- 005 canonical production persistence
- 006 canonical movement integrity
- 007 canonical production reconciliation
- 008 EA-35 idempotency compatibility
- 009 movement integrity hardening
- 010 settlement binding fix

The production schema guard requires the canonical tables, lifecycle states, movement integrity constraints, and settlement/escrow binding contract before runtime construction proceeds.

## Important limitation
These results are strong repository-level technical evidence. They are not an external certification, production operational sign-off, or independent third-party audit.

EA-35 remains IN PROGRESS / NOT LOCKED until the remaining independent re-performance, operational governance, privileged-access/IAM evidence, and final release evidence gates are closed.
