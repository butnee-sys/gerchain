# EA-35.13 Production PostgreSQL Re-performance Gate

Status: IN PROGRESS / NOT LOCKED

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

The factory's current initialization uses SQLAlchemy `metadata.create_all()`. The repository also contains `postgres/migrations.py`, whose `apply_migrations()` implements versioned SQL migrations with advisory locking and checksums.

The currently inspected legacy migration `postgres/schema/001_concurrency.sql` defines an `escrows` table restricted to:

`CREATED, LOCKED, RELEASED`

while the canonical durable Escrow aggregate requires:

`CREATED, FUNDED, LOCKED, RELEASED, REFUNDED, CANCELLED`

Therefore a real PostgreSQL production re-performance cannot yet be declared verified merely from the repository construction path. `create_all()` is not a substitute for versioned production migration validation, and existing SQL schema evidence is not sufficient to prove the full canonical lifecycle.

## Release gate

Do not declare GREEN until all are evidenced against the exact branch tip:

- PostgreSQL database starts successfully.
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
