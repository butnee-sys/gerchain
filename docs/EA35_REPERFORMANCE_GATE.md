# EA-35 PostgreSQL Re-performance Gate

Status: IN PROGRESS / NOT LOCKED

This document records the production re-performance gate. It is not a GREEN declaration.

## Required evidence

1. PostgreSQL 16 migration/concurrency suite passes.
2. Canonical production runtime boots against PostgreSQL.
3. Canonical Ledger is authoritative at runtime.
4. Durable escrow lifecycle is exercised: CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL.
5. Settlement uses the Canonical Ledger.
6. Deep value-truth reconciliation reports no issues.
7. Idempotent replay does not duplicate value movement.
8. Production entrypoint construction matches ProductionRuntimeFactory's actual instance API.
9. Evidence is tied to the exact branch-tip commit.

## Previously observed failures

The October 2026 GitHub Actions evidence included an older migration-runner duplicate-key failure during concurrent migration and an older runtime syntax failure. These observations are retained as historical evidence only; they must be re-run against the current branch tip before any conclusion is made.
