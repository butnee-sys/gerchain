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

Status before CI execution: **UNVERIFIED**.
