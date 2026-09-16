# CORE W3.1 — Production DDL Migration Authority Contract

## Scope

CORE only. SHUUD is explicitly out of scope.

This contract closes the architectural boundary between the canonical schema/version authority established by W3 and the actual PostgreSQL DDL that changes the production schema.

## Problem statement

A recorded schema version is not sufficient evidence that the database has that schema. `create_all`, startup ordering, branch state, application metadata, or a separate DDL path must not silently become an alternative schema authority.

W3.1 therefore requires one authoritative migration path whose execution is bound to the canonical schema authority and whose result is checked against the actual database schema.

## Canonical migration identity

A migration is identified by:

`MigrationIdentity = (MigrationID, SchemaID, FromVersion, ToVersion, MigrationHash)`

`MigrationHash` identifies the exact declared migration definition/DDL payload. A changed migration definition is a different identity even when `MigrationID` is reused.

The authoritative execution record must retain the identity, execution status, timestamps, and resulting schema-state hash.

## Authority rule

A migration may execute DDL only after the canonical schema row has been serialized and the exact predecessor has been validated:

`CanonicalCurrentVersion == Migration.FromVersion`

The executor may not publish a successor schema authority independently of the migration authority transaction.

## Required invariants

### I1 — Single authoritative execution

For one migration identity, at most one authoritative DDL execution may occur.

### I2 — Exact predecessor

A migration whose predecessor does not equal the current authoritative version must be rejected before DDL execution.

### I3 — Idempotent committed retry

Retrying the same migration identity after an authoritative commit returns the existing result and does not execute DDL again.

### I4 — Identity conflict

The same `MigrationID` with a different migration hash or transition is a hard conflict. It must not be treated as an idempotent retry.

### I5 — Failure containment

If DDL execution fails before the successor schema is fully committed, the authoritative predecessor remains authoritative. No false successor version may be published.

### I6 — Concurrent migration serialization

Concurrent migrations from the same predecessor must serialize on the canonical schema authority. At most one may become authoritative.

### I7 — Reader safety

Readers must observe only committed authoritative schema state. An in-progress migration must not be represented as a committed successor.

### I8 — Actual-schema reconciliation

The recorded schema state must be independently comparable with the actual PostgreSQL schema descriptor. A mismatch is an assurance failure, not a value to be averaged or ignored.

### I9 — No bypass

No production DDL path may change an authoritative production schema without a migration identity and schema-authority decision.

### I10 — Retry after failure

A failed migration may be retried only after the actual database and canonical authority are reconciled. Retry logic must not guess whether an ambiguous DDL operation committed.

## Required execution chain

`Migration Definition → Migration Hash → Migration Identity → Schema Authority Lock → Predecessor Validation → DDL Execution → Actual Schema Verification → Atomic Authority Commit → Evidence`

The implementation must make the boundary between DDL execution and transaction commit explicit. PostgreSQL transactional DDL must be used where the migration is compatible with transactional execution; operations that cannot safely participate in one atomic transaction require an explicit compatibility and recovery contract rather than being silently treated as atomic.

## Falsification tests

The following cases must be executable against PostgreSQL:

1. two concurrent executions of the same migration identity;
2. two concurrent distinct migrations from one predecessor;
3. stale predecessor;
4. same migration ID with altered hash;
5. DDL failure before commit;
6. retry after committed success;
7. retry after failure;
8. reader during uncommitted migration;
9. actual schema differs from recorded schema state;
10. direct/bypass DDL attempt without migration authority;
11. migration identity exists but actual DDL was not applied;
12. actual DDL changed but authority record was not committed.

## Independent assurance

The independent oracle must not import GerChain production persistence or migration execution code. It evaluates identity, predecessor, concurrency, idempotency, failure, and reconciliation semantics from an independently defined model.

Independent PostgreSQL re-performance must execute the critical scenarios against an isolated schema using only the declared database contract and independent implementation logic.

## Evidence requirement

W3.1 cannot become GREEN from code review or unit tests alone. Required evidence is:

- CI execution on the exact implementation commit;
- adversarial PostgreSQL test output;
- independent oracle output;
- deterministic reproduction;
- independent PostgreSQL re-performance;
- actual-schema verification evidence;
- evidence record bound to commit, schema, configuration, seed/input, oracle version, runtime identity, result, timestamp, and hash.

## Closure rule

`W3.1_GREEN = CI_GREEN ∧ Oracle_GREEN ∧ Reproduction_GREEN ∧ IndependentPG_GREEN ∧ ActualSchema_GREEN ∧ Evidence_RECONCILED`

W3.1 GREEN remains bounded to the explicitly tested PostgreSQL versions, migration classes, runtime, and declared domain. It does not by itself imply final CORE GREEN or G86 LOCK.

## Architectural non-claim

This contract does not select Alembic, a custom migration engine, or another framework. Before implementation, every existing production DDL/schema initialization path must be mapped and either retired, delegated to this authority, or explicitly classified as non-production.
