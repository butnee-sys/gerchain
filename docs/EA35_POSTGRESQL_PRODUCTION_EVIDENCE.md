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
