# EA-35.14 — Production Entry Point Verification Gate

Status: IN PROGRESS / NOT LOCKED  
Scope: Production runtime construction and schema gate only. This document does not assert production readiness.

## Source-level facts verified on the branch

- `production_entrypoint.py` validates that `GERCHAIN_DATABASE_URL` uses a PostgreSQL scheme.
- It requires `GERCHAIN_ESCROW_ID`, `GERCHAIN_ESCROW_AMOUNT`, `GERCHAIN_CURRENCY`, and `GERCHAIN_WITNESS_ID`; amount must parse as a positive integer.
- `build_production_runtime()` constructs `ProductionRuntimeConfig`, instantiates `ProductionRuntimeFactory`, calls the instance method `create()`, and checks `runtime.is_canonical_ledger_authoritative`.
- The engine is disposed if runtime construction raises, and disposed on normal shutdown.
- `ProductionRuntimeFactory` rejects non-PostgreSQL URLs/engines, applies migrations, checks required table names, checks the recorded migration version is at least 13, configures the canonical ledger, and calls `require_canonical_ledger_authority()`.

## What this evidence does not prove

- That migrations 1–13 apply successfully to a clean, real PostgreSQL instance.
- That migrations safely upgrade a populated production database.
- That all runtime paths (CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, READ) preserve the intended single-transaction boundary on PostgreSQL.
- That crash/restart recovery, idempotent replay, witness/outbox consistency, and deep reconciliation pass against PostgreSQL.
- That CI has executed successfully for the exact commit.
- That an independent party has reproduced the result.

## Required FINAL LOCK gates

1. Run the exact branch commit through repository CI; retain the exact commit SHA and job/run identifiers.
2. Start a clean PostgreSQL instance and apply migrations from zero.
3. Run upgrade-path migration tests against a representative prior schema and populated fixture.
4. Boot `production_entrypoint.py` with valid environment configuration; verify invalid configuration fails closed.
5. Execute the full escrow lifecycle and settlement/read paths against PostgreSQL.
6. Inject rollback, duplicate replay, conflicting idempotency key, missing witness/outbox, and process-restart cases.
7. Run `deep_reconcile_value_truth` after each test scenario; retain machine-readable reports.
8. Confirm legacy stores and alternate runtimes cannot mutate production value.
9. Obtain independent re-performance and record its evidence.
10. Only then approve and record FINAL LOCK.

## Decision rule

No CI run, unavailable CI evidence, SQLite-only tests, or source inspection alone may be reported as production GREEN. Any missing required gate keeps the overall status IN PROGRESS / NOT LOCKED.
