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

## 2026-09-29 evidence reconciliation

A real PostgreSQL 16 GitHub Actions proof is independently observable for commit `95def6bc5d76fd40034b42de858c6dc7dd9bdf5e`:

- workflow: `production-postgresql-proof`
- run: `36384457138`
- job: `postgres-proof`
- conclusion: SUCCESS
- test: `tests/integration/test_production_postgresql_proof.py -m integration`
- result: `1 passed`

The job log confirms a live PostgreSQL 16 service, psycopg installation, and successful production PostgreSQL proof execution.

The current branch tip is `923d5ddac04e3c0a78b93e3b572f6349c3965d25`. Its PostgreSQL production workflow run `36407395414` is currently QUEUED, therefore the historical successful proof is not promoted to exact-current-SHA proof.

**Current evidence state: VERIFIED HISTORICAL POSTGRESQL PROOF / CURRENT-TIP GATE PENDING / NOT LOCKED.**
