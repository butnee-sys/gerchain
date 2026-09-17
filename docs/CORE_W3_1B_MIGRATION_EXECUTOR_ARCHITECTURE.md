# CORE W3.1-B — Production DDL Migration Executor Architecture

**Status:** DESIGN / NOT GREEN
**Scope:** GerChain CORE only
**SHUUD:** Out of scope
**Precondition:** W3.1-A bounded GREEN

## 1. Architecture decision

GerChain will use a **CORE-owned PostgreSQL migration executor** bound directly to the existing W3 Schema Authority. No second migration authority will be introduced.

A migration framework may be used later as a DDL-definition helper, but it cannot own production schema version, predecessor validation, migration identity, or authoritative commit semantics. The W3 Schema Authority remains the sole authority for canonical schema version.

## 2. Authority topology

```text
Migration Definition
        |
        v
Migration Identity + Hash
        |
        v
W3 Schema Authority
        |
        | FOR UPDATE / exact predecessor
        v
W3.1-B Migration Executor
        |
        | transactional PostgreSQL DDL
        v
Actual PostgreSQL Schema
        |
        v
W3.1-A Schema Reconciler
        |
        v
Physical Schema Fingerprint
        |
        v
Atomic Authority Commit
        |
        v
Evidence
```

## 3. Ownership boundaries

### W3 Schema Authority
Owns:
- SchemaID
- authoritative current version
- authoritative state hash
- predecessor transition
- migration identity record
- serialization of competing upgrades

Does not own raw DDL execution.

### W3.1-B Migration Executor
Owns:
- validating a declared MigrationIdentity
- acquiring/retaining the W3 authority transaction
- executing only declared PostgreSQL DDL
- preventing direct executor bypass
- invoking actual-schema verification before authority publication
- containing DDL failure inside the transaction where PostgreSQL permits transactional DDL

Does not independently advance schema authority.

### W3.1-A Reconciler
Owns:
- read-only observation of actual PostgreSQL schema
- canonical logical descriptor
- PhysicalSchemaFingerprint
- MATCH/MISMATCH classification

It cannot repair the database or modify authority.

## 4. Transaction boundary

For transactional PostgreSQL migration classes, the authoritative transaction is:

`BEGIN → lock canonical schema row → validate identity/predecessor → execute DDL → observe actual schema → verify expected physical fingerprint → write migration result + successor authority → COMMIT`

Any failure before COMMIT must leave the predecessor authoritative.

A migration class that cannot safely execute inside this boundary is **OUT_OF_DOMAIN / BLOCKED** until an explicit recovery contract exists. It must not be silently treated as atomic.

## 5. Identity rules

`MigrationIdentity = (MigrationID, SchemaID, FromVersion, ToVersion, MigrationHash)`

Rules:

1. same identity + same hash + committed result → idempotent result, no second DDL execution;
2. same MigrationID + different hash → hard conflict;
3. same predecessor + distinct migration identities → serialized by the canonical schema row;
4. stale predecessor → reject before DDL;
5. successor authority may be published only after actual-schema verification succeeds.

## 6. Migration definition

A migration definition is immutable once its hash is bound to a MigrationIdentity.

The executor receives a typed migration definition rather than arbitrary SQL from an application request. The first implementation scope should be deliberately small: transactional PostgreSQL DDL operations whose expected resulting logical schema can be represented by the W3.1-A v1.1 descriptor.

## 7. Bypass boundary

The executor API must be the only CORE code path permitted to perform production migration DDL.

`create_all()` is not a migration executor. Existing application initialization paths must therefore be classified as test/bootstrap/non-production or removed/delegated before W3.1-B can close the no-bypass invariant.

Direct ad-hoc DDL from application code is prohibited for the production schema.

## 8. Recovery semantics

A failed transaction is safe only when PostgreSQL confirms rollback and W3 authority remains at the predecessor.

An ambiguous external failure must not be retried automatically. Recovery first performs actual-schema reconciliation against the recorded predecessor. Only after reconciliation establishes a known state may retry proceed.

## 9. Initial migration class

The first assurance-grade migration class will be limited to ordinary transactional PostgreSQL DDL represented by W3.1-A v1.1:

- CREATE TABLE
- ADD COLUMN
- ALTER COLUMN TYPE where PostgreSQL transaction semantics permit it
- ALTER COLUMN NULLABILITY
- DEFAULT changes
- PRIMARY KEY
- UNIQUE
- CHECK
- FOREIGN KEY
- standard standalone indexes

Unsupported objects remain outside the first W3.1-B domain.

## 10. Required implementation modules

Planned separation:

- `core/migration_identity.py` — immutable migration identity/domain validation
- `persistence/migration_executor.py` — PostgreSQL transactional executor bound to W3 authority
- `persistence/schema_reconciler.py` — production read-only adapter for W3.1-A logical schema observation
- `tests/test_migration_identity.py` — pure domain tests
- `tests/test_postgres_migration_executor.py` — adversarial PostgreSQL tests
- `tests/independent/w3_1b_independent_oracle.py` — independent semantic oracle
- `tests/independent/w3_1b_postgres_reperformance.py` — independent PostgreSQL reproduction

No module may import an independent oracle into production code.

## 11. Falsification gate

W3.1-B implementation is not GREEN until all contract cases pass:

`F1 same identity concurrency`
`F2 distinct predecessor concurrency`
`F3 stale predecessor`
`F4 altered hash conflict`
`F5 DDL rollback`
`F6 committed retry`
`F7 retry after failure`
`F8 reader safety`
`F9 actual-schema mismatch`
`F10 bypass rejection`
`F11 identity without DDL`
`F12 DDL without authority commit`

## 12. Closure rule

`W3.1-B_GREEN = ArchitectureFrozen ∧ IdentityPASS ∧ ExecutorPASS ∧ F1-F12PASS ∧ OraclePASS ∧ IndependentPGPASS ∧ ActualSchemaPASS ∧ EvidenceReconciled`

This architecture document does not claim implementation, production deployment, or GREEN status.
