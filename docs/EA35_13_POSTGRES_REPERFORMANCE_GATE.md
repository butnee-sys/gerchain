# EA-35.13 Production PostgreSQL Re-performance Gate

Status: IN PROGRESS / NOT LOCKED

Current branch-tip under verification: `70173bf744db60402b4c0a6c4b71358c1c63d3ef`

## Verified repository facts

Branch: `feat/ea21-transaction-aware-ledger`

Production entrypoint commit:
`e860f502f3e1a2d56fd873ad2faab7b1ab630740`

### Construction-path verification

The previous production entrypoint called `ProductionRuntimeFactory.create(...)` as if it were a class-level constructor and passed arguments that do not match the repository's actual `create(self)` method.

The corrected entrypoint now constructs:

1. `ProductionRuntimeConfig`
2. `ProductionRuntimeFactory(config, engine=...)`
3. `factory.create()`

The factory now attaches `configure_canonical_ledger(session_factory)` and requires canonical ledger authority.

### Blocking evidence

The factory now applies the versioned SQL migration chain from `postgres/schema` using `postgres.migrations.apply_migrations()` and then calls `assert_canonical_production_schema()`.

The canonical migration chain already present on the branch contains migrations 001 through 008; the duplicate version-002 file introduced during this verification pass was removed because the migration loader rejects duplicate versions.

The production schema guard requires the canonical Ledger, Escrow, Witness, Outbox, and Durable Idempotency tables/columns and all six escrow states. This closes the previously identified construction-path/schema-definition gap at code level.

This still does not constitute execution-level proof. A fresh PostgreSQL run against the current branch tip is required because the last recorded successful PostgreSQL evidence was against an earlier SHA.

## Release gate

Do not declare GREEN until all are evidenced against the exact branch tip:

- PostgreSQL database starts successfully against the current branch tip.
- Versioned migrations apply successfully.
- Canonical Ledger tables exist and are usable.
- Canonical Escrow full lifecycle schema exists.
- Witness, Outbox, and Durable Idempotency persistence exist.
- Production entrypoint boots and establishes canonical authority.
- FUND → LOCK → RELEASE / REFUND / CANCEL execute against PostgreSQL.
- SETTLEMENT and READ use Canonical Ledger.
- Deep Value Truth Reconciliation returns matched.
- Restart/recovery does not duplicate value movement.
- CI evidence is attached to the exact tested commit.
- Independent re-performance confirms the same result.

Current conclusion: **BLOCKED FOR PRODUCTION LOCK — evidence gap, not a claimed runtime failure.**

## Current verification gate — 2026-09-26

- ProductionRuntimeFactory now constructs and requires Canonical Ledger authority.
- Production entrypoint now uses `ProductionRuntimeFactory.from_engine(...)`.
- Versioned PostgreSQL migrations and the canonical production schema guard run before runtime construction.
- This document does not declare GREEN until a fresh GitHub Actions PostgreSQL execution is observed for this branch/commit.


## Re-performance rerun trigger — 2026-09-26

The first real PostgreSQL run exposed two test-contract defects; both were corrected without changing the production authority boundary. This commit triggers a fresh execution for confirmation.

## Fresh PostgreSQL evidence — 2026-09-26

Exact branch-tip tested: `70173bf744db60402b4c0a6c4b71358c1c63d3ef`.

Observed GitHub Actions results for that exact SHA:
- `Production PostgreSQL Runtime` — run `36166230718` — SUCCESS. The job booted `production_entrypoint.py` against PostgreSQL with the required production environment and then ran production PostgreSQL value-flow tests.
- `PostgreSQL production proof` — run `36166230788` — SUCCESS. The job executed the canonical PostgreSQL flow proof.
- `PostgreSQL production re-performance` — run `36166230598` — SUCCESS. The job executed `tests/integration/test_production_postgresql_reperformance.py`.
- `production-postgresql-runtime` — run `36166230664` — SUCCESS. The job completed both production-entrypoint boot and production value-flow proof.
- `production-postgres-smoke` — run `36166230683` — SUCCESS. Production factory boot and deep reconciliation tests completed.
- `CodeQL Advanced` — run `36166230621` — SUCCESS.
- `security/snyk` commit status — SUCCESS.

The successful re-performance test proves on PostgreSQL:
`ProductionRuntimeFactory.create()` → Canonical Ledger authority → FUND → LOCK → RELEASE → durable balances → RELEASED escrow → `deep_reconcile_value_truth().matched == True`.

The successful production-runtime job additionally proves the actual production entrypoint reaches controlled timeout after successful initialization, rather than exiting early.

Important non-green evidence:
- `core-gates` — run `36166230702` — FAILURE. Its failing step is the broad core structure/boundary test suite. The available job-step metadata does not expose the individual failing assertion, so this is not classified further without logs.
- `production-postgres-reperformance` — run `36166230715` — FAILURE at dependency-install step before its pytest step. This is a workflow/setup failure, not evidence that the PostgreSQL value-flow test failed; a separate production re-performance workflow succeeded as recorded above.

Conclusion for EA-35.13:
**PostgreSQL runtime re-performance is VERIFIED for the tested value-flow scope, but the overall production lock remains NOT LOCKED because broad core-gates and remaining lifecycle/recovery evidence are not yet closed.**
