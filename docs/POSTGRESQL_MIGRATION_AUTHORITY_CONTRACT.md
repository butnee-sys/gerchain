# PostgreSQL Migration Authority — Production Contract

Status: ACTIVE CONTRACT / PRODUCTION NOT LOCKED

## Single authoritative migration path

Production PostgreSQL schema initialization MUST call
`services.gerchain_runtime_factory.initialize_canonical_postgres_schema()`.
That function calls `postgres.migrations.apply_migrations()` over
`postgres/migrations/001_canonical_production.sql` through
`016_reconcile_escrow_state_constraint.sql`, then performs ORM metadata
creation and `assert_canonical_production_schema()`.

The numbered files in `postgres/migrations/` are the only authoritative,
versioned production migration chain. The migration runner serializes execution
with a PostgreSQL transaction-scoped advisory lock, checksums each canonical
migration, and records applied versions in `schema_version`.

## Legacy schema path

`postgres/schema/001_concurrency.sql` is a historical/legacy schema artifact.
It MUST NOT be invoked by production boot, CI migration setup, or operational
migration instructions. It is not a second migration stream and is not evidence
that the canonical 001–016 chain has been applied.

Do not copy DDL between these paths as an operational workaround. Any production
schema change must be introduced as the next numbered canonical migration,
added to the explicit registry in `postgres/migrations/__init__.py`, and
covered by migration-upgrade tests.

## ORM metadata creation

SQLAlchemy `metadata.create_all()` runs only after the numbered migration
runner. It can ensure model-owned tables exist but MUST NOT be treated as a
substitute for versioned DDL, constraint validation, data backfill, or migration
history. Production boot must fail closed if the required 16 migration versions,
columns, or validated constraints are absent.

## Required PostgreSQL evidence

A passing SQLite test is not PostgreSQL evidence. Before EAI or the fundamental
architecture can be production-locked, CI must execute on PostgreSQL:
1. fresh database migration through versions 001–016;
2. repeated migration application and checksum/history validation;
3. two or more concurrent value movements contending for the same accounts;
4. deterministic account locking, no negative balances, no duplicate movement;
5. failed transaction rollback and idempotent replay/conflict behavior;
6. runtime factory boot against that migrated database;
7. deep value-truth reconciliation after the concurrent run.

The evidence must identify the exact tested commit SHA and actual GitHub Actions
run/job result. Missing or unavailable checks are UNVERIFIED, never GREEN.
