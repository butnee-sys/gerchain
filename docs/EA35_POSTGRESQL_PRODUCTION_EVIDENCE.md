# EA-35 PostgreSQL Production Evidence

## Scope

This record covers the canonical PostgreSQL production runtime and value-truth boundary on the exact branch execution commit.

## Exact execution commit

- Branch: `feat/ea21-transaction-aware-ledger`
- Commit: `214c158a24ae97cd8a0ac8a1af708ac9042b2481`
- Execution date: 2026-09-29
- PostgreSQL service: PostgreSQL 16
- Python: 3.13

## Verified workflow evidence

The following GitHub Actions runs were associated with the exact execution commit and completed successfully:

| Gate | Run | Result |
|---|---:|---|
| PostgreSQL Production Gate | 36519670647 | SUCCESS |
| PostgreSQL production re-performance | 36519670742 | SUCCESS |
| production-postgresql-e2e | 36519670670 | SUCCESS |
| Production PostgreSQL verification | 36519670609 | SUCCESS |
| PostgreSQL Production Evidence | 36519670616 | SUCCESS |
| production-postgres-gate | 36519670645 | SUCCESS |
| Production PostgreSQL Smoke | 36519670610 | SUCCESS |
| production-postgresql | 36519670654 | SUCCESS |

### Direct re-performance evidence

Run `36519670742`, job `109249554498`:

- PostgreSQL 16 service initialized and accepted connections.
- Python 3.13 environment initialized.
- Production dependencies installed.
- `tests/integration/test_postgresql_production_reperformance.py` executed.
- Result: **1 passed in 0.34s**.

This is direct execution evidence against a real PostgreSQL service, not SQLite substitution.

## Runtime construction verified

The production factory now:

1. requires a PostgreSQL URL;
2. applies versioned PostgreSQL migrations;
3. validates the canonical production schema;
4. constructs `GerchainRuntime`;
5. attaches `configure_canonical_ledger()`;
6. requires Canonical Ledger authority before returning the runtime.

The production entrypoint constructs `ProductionRuntimeConfig` and `ProductionRuntimeFactory` using the actual PostgreSQL DSN; it no longer calls a nonexistent class-level factory constructor.

## Evidence interpretation

This evidence establishes that the canonical PostgreSQL runtime and the EA-35 production re-performance test execute successfully on the exact commit above.

It does **not** by itself establish final system-wide production lock. Remaining gates include:

- independent re-performance by a separate reviewer/environment;
- complete evidence reconciliation against the final release candidate;
- organizational IAM/MFA and privileged-access evidence where applicable;
- final architecture/production lock decision.

No certification or external audit claim is made by this document.

## 2026-10-02 gate reconciliation

The earlier workflow execution on commit e860f502f3e1a2d56fd873ad2faab7b1ab630740 was not accepted as production evidence. Its PostgreSQL Concurrency run 36542458201 failed in the migration serialization test with a duplicate schema_version row, while core-gates run 36542458205 failed during collection because that execution contained a malformed runtime source block.

The current branch contains the corresponding corrections: the migration runner deterministically selects one canonical file per duplicated historical migration version, records migration versions idempotently with checksum verification, and the runtime FUND method source is valid Python again. A fresh exact-SHA workflow execution is required before any GREEN/LOCK claim.

Status: IN PROGRESS / NOT LOCKED.

## Current branch-tip verification gate

- Current branch tip: `4a705c1bd4c977c1c6bada90180661a2ad3211c3`
- The historical successful merge-ref runs above are retained as historical evidence only.
- A new pull-request execution against the current branch tip is required before promoting this evidence to current-tip GREEN.


## Latest production verification

The pull-request merge ref containing `2a2fef2ac9bda92052899fe9c1507159e89ca1b8` was executed as merge commit `430e41233b4158669feff04c9a7d2f056fcc6235`.

Successful runs on that merge ref include:

- Production PostgreSQL verification — run `36706455431`: lifecycle, canonical value flow, and deep reconciliation all succeeded.
- PostgreSQL Production Evidence — run `36706455516`: production PostgreSQL boot evidence succeeded.
- production-postgres-gate — run `36706455517`: runtime construction and deep value-truth reconciliation succeeded.
- production-postgresql-e2e — run `36706455530`: production PostgreSQL re-performance succeeded.

The direct verification job recorded: lifecycle **1 passed**, production value-flow **2 passed**, and deep reconciliation **19 passed**.

## Current gate

Commit `ede6c10f48bf9a193d5719864cf6cc60d287c5bc` adds the historically observed version-1 checksum `494763e210c8a3839972ba21e8705dcf2e6564e5abca9c76161f2f49c6664ec8` to the migration compatibility set. Fresh PostgreSQL/EAI/core workflows are queued for this commit.

Status remains **IN PROGRESS / NOT LOCKED** until those fresh runs complete. No GREEN or production-lock claim is made from queued evidence.
