# EA-35.13 — Exact-SHA PostgreSQL Re-performance Record

**Status: IN PROGRESS / NOT LOCKED**  
**Repository:** `butnee-sys/gerchain`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Evidence commit under test:** `87a643ffeed72eb2374d000939eb6e1cc58c71cb`  
**Evidence date:** 2026-10-12 (GitHub Actions UTC)

## Dedicated gates that passed on the exact SHA

| Workflow | Run ID | Result | Evidence |
|---|---:|---|---|
| EAI PostgreSQL Re-performance | 38238957220 | PASS | 49 tests passed; migration history marker PASS; deep value reconciliation suite: 19 passed |
| PostgreSQL Migration and Production Proof | 38238957204 | PASS | migration concurrency: 3 passed; migration rollback: 1 passed; PostgreSQL production runtime factory: 1 passed |
| Production PostgreSQL Gate | 38238957122 | PASS | focused production PostgreSQL re-performance + deep reconciliation: 4 passed; migration concurrency: 4 passed |
| PostgreSQL migration gate | 38238957336 | PASS | GitHub Actions run completed successfully |
| Canonical PostgreSQL Migration Gate | 38238956997 | PASS | GitHub Actions run completed successfully |
| PostgreSQL migration idempotency | 38238957161 | PASS | GitHub Actions run completed successfully |

These results support the focused PostgreSQL runtime, migration, and deep-reconciliation paths on this SHA. They do not, by themselves, establish full-repository production readiness.

## Exact-SHA gates that remain failing

| Workflow | Run ID | Result | Observed failure |
|---|---:|---|---|
| FINAL EAI/CORE Exact-SHA Gate | 38238957199 | FAIL | Legacy escrow state-constraint drift reproduction step failed; dedicated production-EAI job passed |
| Production Gate | 38238957027 | FAIL | Full test suite: 74 failed, 1,131 passed, 7 skipped, 3 errors |

The broad Production Gate includes environment-dependent PostgreSQL tests that failed because expected database environment variables were absent or pointed at an incompatible local credential, plus API/test-contract mismatches. Reported examples include missing `GERCHAIN_DATABASE_URL`, `GERCHAIN_POSTGRES_DSN`, `GERCHAIN_TEST_DATABASE_URL`; schema-assertion disagreement about legacy escrow state constraints; missing escrow rows in integration setup; and mismatched runtime/test APIs. These are not to be reclassified as passes.

A separate focused production gate did pass, but the broad gate and exact-SHA final gate are still red. This difference must remain visible.

## Four canonical lifecycle behaviors

The focused production PostgreSQL evidence covers a canonical value-flow path and deep reconciliation against a real PostgreSQL service. The local test summary from the dedicated re-performance run reports 4 passed across `tests/postgres/test_production_postgres_reperformance.py` and `tests/persistence/test_deep_value_reconciliation_postgres.py`. The dedicated EAI run also reports 19 passed for `tests/persistence/test_deep_value_reconciliation.py`.

Do not infer that every possible CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT variant is proven by one happy-path result. Keep the four-behavior claim bounded to the named focused tests and their logs; extend the test matrix as needed.

## Production boot and schema

The production factory uses the canonical PostgreSQL migration registry, applies migrations, ensures ORM-owned tables exist, then checks required columns and database constraints before establishing Canonical Ledger authority. The focused PostgreSQL production gate passed. However, the broad gate still reveals failures around legacy escrow constraint repair and multiple production integration fixtures, so migration and boot are not fully locked.

## Decision

- **Focused PostgreSQL value-flow proof:** PASS on the exact SHA.
- **Focused deep value-truth reconciliation:** PASS on the exact SHA.
- **Focused migration/concurrency/rollback checks:** PASS on the exact SHA.
- **Full repository production gate:** FAIL.
- **Final exact-SHA EAI/CORE gate:** FAIL.
- **Production lock:** NOT AUTHORIZED.

## Required next closure steps

1. Repair the legacy escrow constraint drift test and prove the migration removes or reconciles conflicting state constraints without losing existing escrow rows.
2. Consolidate PostgreSQL integration test setup so required DSN variables are consistently provided and isolated from developer-local credentials.
3. Reconcile outdated integration fixtures with the current canonical runtime factory and escrow creation contract; do not weaken production invariants to satisfy stale tests.
4. Re-run the exact-SHA full suite and final EAI/CORE gate.
5. Only after both are green, publish the final evidence index and consider production lock.
