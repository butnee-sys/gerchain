# EA-35 PostgreSQL Production Re-performance

## Scope
This gate verifies the production PostgreSQL runtime against a real PostgreSQL 16 service.

Required evidence:
1. ProductionRuntimeFactory constructs the runtime through Canonical Ledger authority.
2. Canonical persistence tables are created and reachable.
3. FUND and LOCK execute against durable production state.
4. RELEASE executes through the Canonical Ledger and is idempotent.
5. REFUND uses the authoritative escrow refund destination.
6. CANCEL reverses funded value to the authoritative original sender.
7. SETTLEMENT uses the Canonical Ledger rather than an independent balance store.
8. Deep Value Truth Reconciliation remains matched after value operations.
9. No production path silently falls back to MoneyLedger or legacy ReleaseAccount authority.

## Current gate state
Implementation is present. Runtime construction has been corrected so the production entrypoint instantiates ProductionRuntimeFactory with ProductionRuntimeConfig and calls the instance create() method. The factory configures the Canonical Ledger rather than the legacy PostgreSQL Release authority.

The gate is NOT LOCKED until GitHub Actions provides a successful run for the exact branch-tip commit and the resulting test evidence is independently reviewed.

## Required exact-SHA evidence
- Workflow: ea35-postgresql.yml
- Workflow: ea35-production-reperformance.yml
- Workflow: postgresql-production-gate.yml
- PostgreSQL: version 16 service
- Test suites:
  - tests/integration/test_production_runtime_postgresql.py
  - tests/persistence/test_production_runtime_postgres.py
  - tests/persistence/test_deep_value_reconciliation.py

## Lock rule
No GREEN/LOCKED claim is permitted from source inspection alone. A fresh successful GitHub Actions result for the exact commit is required.