# CORE W3 — Discovery Evidence

## Date

2026-09-16

## Scope

CORE only. SHUUD excluded.

## Discovery result

The current repository does not expose a dedicated schema-version authority or migration subsystem under the expected names searched during W3 discovery (`schema_version`, `migration`, `upgrade`, or Alembic configuration).

The inspected `database.py` defines SQLAlchemy models for `gerchain_escrow_states` and `gerchain_chain_tips`, creates an engine, and initializes tables through `Base.metadata.create_all(engine)`. No schema-version state machine, predecessor-version check, migration journal, or concurrent upgrade protocol is present in that file.

The repository test fixture similarly initializes the database through `Base.metadata.create_all(bind=engine)` and later drops metadata. This establishes table creation for tests, but it is not evidence of a concurrent schema migration/version authority.

## W3 consequence

W3 cannot be marked GREEN from the current implementation evidence.

The current evidence is insufficient to establish:

- single authoritative schema version;
- atomic version transition;
- predecessor/version compare-and-set semantics;
- concurrent migration conflict isolation;
- reader safety during migration;
- migration rollback/recovery;
- schema upgrade idempotency.

## Status

**W3 = INCONCLUSIVE / IMPLEMENTATION GAP**

This is not a claim that the whole CORE is RED. It is a gate-local finding: the declared W3 schema-concurrency capability has not yet been demonstrated by an identifiable production implementation.

## Required next step

Before W3 tests are treated as implementation validation, define and implement (or explicitly identify an existing authoritative mechanism for):

1. canonical schema identity;
2. current schema version;
3. atomic predecessor-to-successor transition;
4. migration identity and idempotency;
5. concurrent upgrade serialization/conflict handling;
6. reader compatibility boundary;
7. rollback/recovery semantics;
8. independent oracle and reproduction contract.

Only after these are explicit should adversarial PostgreSQL tests be promoted to W3 closure evidence.
