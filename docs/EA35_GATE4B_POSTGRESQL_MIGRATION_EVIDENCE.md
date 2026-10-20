# EA-35.14 — Gate 4B PostgreSQL Migration and Runtime Evidence

Status: **OPEN / NOT LOCKED**
Branch: `feat/ea21-transaction-aware-ledger`

## Purpose

This record separates production runtime construction from database migration and records the repository-level checks required before PostgreSQL production re-performance can be accepted.

## Findings verified from repository source

1. `production_entrypoint.py` constructs `ProductionRuntimeConfig`, creates `ProductionRuntimeFactory`, and calls its instance `create()` method.
2. `services/gerchain_runtime_factory.py` initializes persistence models with SQLAlchemy `metadata.create_all()`. This is table creation support, not a substitute for applying and validating versioned schema migrations to existing installations.
3. `postgres/schema/001_concurrency.sql` creates the canonical ledger, witness, outbox and idempotency tables and adds escrow aggregate columns with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
4. The migration file backfills `created_at` and `refund_destination` before setting `created_at NOT NULL`; `currency` remains nullable in the shown migration although the runtime model and canonical escrow operations expect a currency value.
5. The escrow state check constraint in the migration includes `CREATED`, `FUNDED`, `LOCKED`, `RELEASED`, `REFUNDED`, and `CANCELLED`. This must be verified on both clean and pre-existing schemas rather than inferred from the SQL text alone.
6. No actual PostgreSQL execution result is available in this evidence record. Therefore no claim is made that migrations, boot, lifecycle operations, or deep reconciliation have passed on a real PostgreSQL instance.

## Gate 4B required evidence

- Run the exact migration sequence against a clean PostgreSQL database.
- Run the same migration sequence against a representative pre-existing schema.
- Query PostgreSQL catalog metadata to assert required columns, nullability, unique constraints, check constraints, and indexes.
- Verify currency and all other required escrow fields are non-null and populated for migrated rows.
- Boot the production entrypoint with PostgreSQL and assert the runtime reports canonical Ledger authority.
- Exercise the lifecycle operations and inspect durable rows in the same database.
- Run deep value-truth reconciliation and require zero unexplained issues.
- Capture all results against the same commit SHA and preserve logs/artifacts.

## Release decision

**Gate 4B remains OPEN.** Source inspection is not runtime proof. `metadata.create_all()` must not be treated as migration evidence. Production readiness must not be declared until clean-schema and upgrade-schema PostgreSQL runs both pass and are tied to one commit.
