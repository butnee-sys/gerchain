# EA-35.13 PostgreSQL Re-performance — 2026-10-04

## Verification finding

The PostgreSQL service initialized successfully in the 2026-10-03 core-gates run. The gate failed during Python test collection because `services/gerchain_runtime.py` contained a malformed literal newline sequence, producing a SyntaxError.

## Correction status

The current `feat/ea21-transaction-aware-ledger` branch was re-read after the failed run. The affected runtime methods are now stored as valid Python source and the production factory is wired to `configure_canonical_ledger()`.

## Required fresh evidence

A new push-triggered PostgreSQL production gate must pass all of:
1. Python syntax compilation.
2. ProductionRuntimeFactory PostgreSQL construction.
3. Canonical schema migration and schema guard.
4. Canonical Ledger movement.
5. Idempotent replay.
6. Deep value-truth reconciliation.

## Lock rule

EA-35 remains IN PROGRESS / NOT LOCKED until a fresh exact-SHA GitHub Actions PostgreSQL gate completes successfully and the result is independently reviewed.

## Fresh execution trigger — 2026-10-04

This revision is intentionally pushed to trigger the branch PostgreSQL production gates. Historical successful SHA evidence is not reused as current proof. The required decision is based only on the workflow runs attached to the resulting commit.


## Evidence refresh — 2026-10-04

The previously recorded exact-SHA production evidence for 35f7026e78f42a8e57229989b3db0ea0f95e204f was re-queried from GitHub Actions. The following completed successfully: PostgreSQL production re-performance, Production PostgreSQL Smoke, PostgreSQL Production Gate, production-postgresql-gate, production-postgres-gate, Production PostgreSQL verification, PostgreSQL Production Evidence, production-postgresql, Canonical EAI PostgreSQL Gate, production-postgresql-e2e, and CodeQL Advanced. SHUUD workflows are outside the current EAI/fundamental production scope. The core-gates run on that SHA was cancelled and is therefore not treated as evidence of success or failure.

This evidence-only revision intentionally makes no architecture or runtime change. A new exact-SHA execution is required before final lock, including the independent PostgreSQL evidence workflow and final repository-wide canonical gates.


## Exact-SHA verification trigger — 2026-10-05

This commit is an evidence-trigger revision only. No production architecture or value-flow behavior is changed here. GitHub Actions must execute the PostgreSQL production and independent evidence gates against this exact commit SHA. Prior successful execution SHAs remain historical evidence and are not substituted for this exact-SHA proof.

**Decision rule:** EA-35 remains NOT LOCKED until the exact-SHA canonical PostgreSQL gates pass and their run IDs are independently re-read.


## Exact-SHA execution trigger — 2026-10-05

This evidence-only revision changes no production architecture, runtime behavior, or value-flow logic. It exists solely to create a fresh push event for the canonical PostgreSQL production gates. Final verification must use only workflow results attached to the resulting exact commit SHA.

Decision rule: EA-35 remains IN PROGRESS / NOT LOCKED until the fresh exact-SHA PostgreSQL production gate and independent evidence workflow are re-read from GitHub Actions.
