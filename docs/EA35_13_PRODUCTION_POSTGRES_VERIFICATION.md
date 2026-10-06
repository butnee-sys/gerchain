# EA-35.13 Production PostgreSQL Verification Record

Status: IN PROGRESS / NOT LOCKED

Execution note: historical CI run 36542458205 failed during collection because of a syntax error in the then-current runtime source; PostgreSQL itself reached ready state. Current runtime source has been re-read and the affected methods are syntactically valid. Fresh push-triggered PostgreSQL execution remains required.

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

## Fresh exact-SHA execution verification — 2026-10-06

Exact execution SHA: `c089b99f5367cb88d58afc194ce9d02ada56b34b`.

Fresh GitHub Actions evidence:
- `production-postgresql-gate` — run `37420557048` — **SUCCESS**.
  - production factory and canonical persistence: SUCCESS
  - production entrypoint boot against PostgreSQL: SUCCESS
  - deep value reconciliation: SUCCESS
  - EAI production re-performance: SUCCESS
  - real PostgreSQL production value-flow gate: SUCCESS
- `production-postgres` — run `37420557024` — **SUCCESS**.
  - PostgreSQL migration and boot: SUCCESS
  - production value flow: SUCCESS
  - deep value truth: SUCCESS
- `independent-postgresql-evidence` — run `37420557156` — **SUCCESS**.
  - independent persisted-value verification: SUCCESS
- `CORE Operating Reconciliation` — run `37420557213` — **SUCCESS**.
- `CodeQL Advanced` — run `37420557095` — **SUCCESS**.

This is execution evidence on the corrected production-runtime construction, not merely source inspection.

### Verdict
**EA-35.13 PostgreSQL production execution: VERIFIED on exact SHA `c089b99f5367cb88d58afc194ce9d02ada56b34b`.**

**Final fundamental-architecture LOCK: NOT YET DECLARED.** The canonical `core-gates` run `37420557044` was still in progress at this evidence refresh. Product/SHUUD workflows are outside the current EAI/fundamental production scope.
