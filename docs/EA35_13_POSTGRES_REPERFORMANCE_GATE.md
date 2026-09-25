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
