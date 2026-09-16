# CORE W3 — Canonical Schema Authority Design

## Purpose

W3 requires a single authoritative schema/version state for GerChain CORE.
The authority is PostgreSQL-backed and must not be inferred from `create_all`,
SQLite projections, application startup order, or Git branch state.

## Canonical records

`core_schema_state`

- `schema_id` — primary key
- `current_version` — authoritative integer version
- `state_hash` — hash of the canonical schema-state descriptor
- `status` — ACTIVE / UPGRADING / FAILED
- `updated_at`

`core_schema_upgrade`

- `upgrade_id` — primary key
- `schema_id`
- `from_version`
- `to_version`
- `migration_hash`
- `authority`
- `status` — REQUESTED / APPLIED / REJECTED / FAILED
- timestamps

## Authority rule

A valid upgrade is accepted only when the locked canonical row still has:

`current_version == upgrade.from_version`

and the upgrade identity has not already been applied.

The predecessor check, migration-state transition, and authoritative version
update must commit in one PostgreSQL transaction.

## Concurrency rule

Two distinct upgrades from the same predecessor compete on the same canonical
schema row. Row-level serialization plus predecessor validation permits at
most one authoritative transition. The losing transaction must reject rather
than overwrite the winner.

The same `upgrade_id` is idempotent: a retry after `APPLIED` returns the
existing authoritative result and must not create another transition.

## Reader boundary

Readers must observe only committed schema state. A migration may not expose
an authoritative version until its associated migration state has committed.
Application execution must refuse a schema status of `UPGRADING` unless an
explicit compatibility contract allows that reader.

## Recovery

A failed migration must leave the authoritative predecessor intact unless a
fully atomic successor was committed. Ambiguous application-level retries are
resolved by re-reading `upgrade_id` and canonical schema state, not by guessing.

## Separation of concerns

- `core/schema_authority.py`: pure state-transition contract.
- PostgreSQL adapter: locking, uniqueness, transaction boundaries.
- Migration executor: applies a declared migration and produces `migration_hash`.
- Independent oracle: evaluates allowed version-transition semantics without
  importing production persistence code.

No SHUUD code or route participates in W3.

## W3 non-claim

Creating this design does not make W3 GREEN. GREEN requires PostgreSQL
adversarial execution, independent oracle agreement, deterministic
reproduction, independent re-performance, and reconciled evidence tied to the
execution commit.
