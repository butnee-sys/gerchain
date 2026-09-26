# EA-35 PostgreSQL Re-performance Status

## Execution gate

This document records the execution gate for EA-35 PostgreSQL re-performance.

Required evidence:
1. PostgreSQL 16 service starts.
2. Versioned production migrations apply successfully.
3. ProductionRuntimeFactory constructs a Canonical Ledger-authoritative runtime.
4. production_entrypoint.py boots against PostgreSQL and remains alive until controlled timeout.
5. PostgreSQL FUND → LOCK → RELEASE executes against the Canonical Ledger.
6. RELEASE replay is idempotent.
7. Deep Value Truth reconciliation reports no issues.
8. Canonical balances and durable escrow state match expected final state.

Status: **PARTIALLY VERIFIED — NOT LOCKED**.

## Executed evidence

- GitHub Actions run: `35891334931`
- Job: `postgres-reperformance`
- Commit SHA: `ad50632f56b3ff4b47dbc6df1eab990e7da13008`
- PostgreSQL: `16.15`
- Python: `3.13.15`
- Executed test: `tests/integration/test_production_postgresql_reperformance.py`
- Result: **1 passed in 0.59s**
- The run used a real PostgreSQL 16 service and the configured `GERCHAIN_DATABASE_URL`.

This proves a real PostgreSQL execution path for the production re-performance test at the cited SHA. It does **not** by itself prove the full CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ matrix, restart/recovery, or independent re-performance.
