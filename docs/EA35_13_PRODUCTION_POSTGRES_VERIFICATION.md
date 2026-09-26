# EA-35.13 Production PostgreSQL Verification Record

Status: IN PROGRESS / NOT LOCKED

Verification target: production runtime construction and PostgreSQL canonical value-flow path.

Verified on branch: `feat/ea21-transaction-aware-ledger`

Verified commit:
`e860f502f3e1a2d56fd873ad2faab7b1ab630740`

## Source-level evidence

1. `ProductionRuntimeFactory` requires a PostgreSQL URL and PostgreSQL engine.
2. Factory initialization applies all files under `postgres/schema` through `apply_migrations`.
3. Factory then executes `assert_canonical_production_schema`.
4. Factory constructs `GerchainRuntime` and configures `configure_canonical_ledger()`.
5. Factory requires `is_canonical_ledger_authoritative`.
6. Production entrypoint constructs `ProductionRuntimeConfig` and calls `ProductionRuntimeFactory.from_engine(...).create()`.
7. Production entrypoint fails closed unless Canonical Ledger authority is established.
8. The branch contains PostgreSQL migrations 001 through 009.
9. The production PostgreSQL workflow includes:
   - factory construction verification;
   - production entrypoint boot against PostgreSQL;
   - PostgreSQL canonical value-flow re-performance;
   - refund/cancel re-performance;
   - deep reconciliation tests;
   - canonical value-flow tests.
10. The independent production PostgreSQL workflow executes `tests/persistence/test_production_runtime_postgres.py`.

## Execution evidence

Fresh execution result for commit `e860f502...` is NOT VERIFIED from the available GitHub connector in this run. The connector exposes pull-request-associated workflow runs, while these workflows are push-triggered on the feature branch.

Therefore this record does not declare CI GREEN and does not declare production lock.

## Required next gate

Obtain the actual GitHub Actions result for the push-triggered PostgreSQL re-performance. Only after the exact commit has a successful run should EA-35.13 move from source-verified to execution-verified.

## Lock rule

No production lock may be declared from source inspection alone.
