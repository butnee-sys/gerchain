# CORE W3.1 — Actual PostgreSQL Schema Reconciliation Contract

## 1. Purpose

This contract defines how recorded CORE schema authority is compared with the actual PostgreSQL schema. It does not execute DDL and does not grant reconciliation any authority to mutate the database.

CORE schema assurance has two distinct dimensions:

`AuthorityIdentity ∧ PhysicalSchemaTruth`

A schema version number alone is insufficient evidence of physical schema state, and a matching physical schema alone is insufficient evidence of authority-chain validity.

## 2. Authority boundary

The authority chain is:

`W3 Schema Authority → W3.1 Migration Executor → PostgreSQL DDL → Actual Schema Reconciler → Evidence`

The reconciler is read-only.

It MUST NOT:

- change schema authority;
- execute DDL;
- repair a mismatch silently;
- infer that a version number proves physical schema identity;
- overwrite recorded state with observed state.

A mismatch is an assurance failure requiring investigation and controlled recovery.

## 3. Validated W3.1 logical schema scope v1.1

The bounded v1.1 domain is:

`TABLE, COLUMN, TYPE, NULLABILITY, DEFAULT, PRIMARY KEY, UNIQUE, CHECK, FOREIGN KEY, STANDARD STANDALONE INDEX`

The following are explicitly outside this validated domain unless a later descriptor version adds them:

`TRIGGER, VIEW, MATERIALIZED VIEW, FUNCTION, PROCEDURE, SEQUENCE, EXTENSION, PARTITIONING, RLS POLICY, EXPRESSION INDEX, PARTIAL INDEX, CUSTOM OPERATOR CLASS, ADVANCED INDEX OPTIONS`

A scope violation is `SCOPE_ERROR` / `OUT_OF_DOMAIN`; it must not be silently treated as a valid physical match.

## 4. Canonical logical schema descriptor

The physical fingerprint is calculated from the logical schema projection within the declared scope:

`LogicalSchema = Projection(ActualPostgreSQLCatalog, DeclaredScope)`

`CLS = (Tables, Constraints, Indexes)`

`Table = (Namespace, Name, Columns, PrimaryKeys, UniqueConstraints, Checks, ForeignKeys)`

`Column = (Ordinal, Name, Type, Nullable, DefaultExpression)`

`Type = (TypeSchema, TypeName, Parameters, ArrayDimensions)`

`PrimaryKey = (ConstraintName, ColumnsInDeclaredOrder)`

`Unique = (ConstraintName, ColumnsInDeclaredOrder)`

`Check = (ConstraintName, Expression)`

`ForeignKey = (ConstraintName, ColumnsInDeclaredOrder, ReferencedTable, ReferencedColumnsInDeclaredOrder, OnUpdate, OnDelete)`

For the bounded standard-index domain:

`Index = (Namespace, Name, Table, Unique, Method, KeyColumnsInDeclaredOrder, IncludedColumnsInDeclaredOrder)`

PK/UNIQUE backing indexes are PostgreSQL implementation artifacts of logical constraints and MUST NOT be double-counted as standalone indexes.

## 5. Canonicalization

Canonicalization MUST:

1. use UTF-8 deterministic serialization;
2. preserve PostgreSQL-resolved identifier identity;
3. sort independent collections deterministically;
4. preserve column ordinal order;
5. preserve composite PK/UNIQUE/FK/index key order;
6. represent null explicitly;
7. use a versioned descriptor serialization;
8. exclude timestamps, PIDs, transaction IDs and physical object identifiers;
9. normalize the bounded type representation deterministically;
10. normalize defaults/check expressions only within the explicitly supported PostgreSQL semantic representation.

Raw catalog row order MUST NOT affect the fingerprint.

The v1.1 implementation does not claim general SQL semantic equivalence for arbitrary expressions; unsupported expression forms are outside the validated domain rather than guessed equivalent.

## 6. Physical schema fingerprint

The physical fingerprint is:

`PhysicalSchemaFingerprint = SHA256(UTF8(CanonicalSerialize(LogicalSchema)))`

SchemaID and DescriptorVersion are NOT components of the physical schema semantics and MUST NOT be hashed into `PhysicalSchemaFingerprint`.

The descriptor version identifies the canonicalization specification, not the observed physical schema itself.

## 7. Authority identity

Authority remains a separate identity:

`AuthorityIdentity = (SchemaID, Version, DescriptorVersion, MigrationIdentity)`

where:

`MigrationIdentity = (MigrationID, SchemaID, FromVersion, ToVersion, MigrationHash)`

Therefore:

`PhysicalSchemaFingerprint != MigrationHash`

and:

`PhysicalSchemaFingerprint equality ≠ AuthorityIdentity equality`

A physically matching database cannot legitimize an unauthorized migration.

## 8. Reconciliation predicate

For recorded state `R` and actual descriptor `A`:

`RECONCILED := R.SchemaID == A.SchemaID ∧ R.DescriptorVersion == A.DescriptorVersion ∧ R.StateHash == PhysicalSchemaFingerprint(A) ∧ ScopeValid`

Authority-chain validity is checked separately:

`AUTHORITY_VALID := Valid(SchemaID, Version, MigrationIdentity, Predecessor, MigrationHash)`

Thus:

`W3.1_ASSURANCE_MATCH := RECONCILED ∧ AUTHORITY_VALID`

A physical match alone does not produce GREEN.

## 9. Reconciliation states

- `MATCH` — physical schema matches the recorded hash within the declared scope and authority identity is separately valid.
- `RECORDED_MISMATCH` — recorded hash exists but actual physical schema differs.
- `ACTUAL_UNEXPECTED` — authoritative-scope object exists without matching recorded authority.
- `RECORDED_MISSING` — authority expects structure absent from actual schema.
- `IDENTITY_MISMATCH` — SchemaID mismatch.
- `VERSION_MISMATCH` — authority version mismatch.
- `DESCRIPTOR_VERSION_MISMATCH` — canonicalization specification mismatch.
- `SCOPE_ERROR` — observed schema cannot be classified under the declared scope.
- `INSPECTION_ERROR` — actual schema could not be reliably observed.

Only `MATCH` with valid authority identity can contribute to W3.1 GREEN.

## 10. Atomic migration expectation

For PostgreSQL transactional DDL:

`BEGIN → Authority Lock → Predecessor Validation → DDL → Actual Schema Verification → Authority Commit → COMMIT`

If verification fails, the successor authority state MUST NOT be published.

Non-transactional DDL requires a separate recovery contract.

## 11. Reader safety

`VisibleAuthorityState ∈ CommittedStates`

Readers may observe the previous committed state during an in-progress migration, but never a partially committed successor.

## 12. Falsification cases

The implementation must eventually falsify at least:

1. exact schema match;
2. column add/remove;
3. type mutation;
4. nullability mutation;
5. default mutation;
6. PK mutation;
7. UNIQUE mutation;
8. CHECK mutation;
9. FK mutation;
10. standalone index mutation;
11. backing-index exclusion;
12. unauthorized out-of-scope object;
13. equal version with unequal fingerprint;
14. equal fingerprint with invalid authority identity;
15. deterministic repeated fingerprinting;
16. fresh-process deterministic replay;
17. rollback after failed DDL;
18. committed retry;
19. inspection failure;
20. scope violation.

## 13. Independent oracle

The independent oracle MUST independently derive the logical descriptor and SHA-256 fingerprint without importing CORE schema authority, migration executor, reconciler or fingerprint implementation.

Required cross-agreement:

`Descriptor_oracle == Descriptor_observer`

and:

`Fingerprint_oracle == Fingerprint_observer`

Any disagreement is non-GREEN.

## 14. Evidence identity

Every assurance run binds:

`(EvidenceID, GateID, RunID, Commit, SchemaID, AuthorityVersion, DescriptorVersion, DeclaredScope, ActualFingerprint, RecordedHash, OracleVersion, RuntimeFingerprint, Timestamp, Verdict, EvidenceHash)`

No evidence lacking these identity fields may support W3.1 GREEN.

## 15. Closure condition

`ActualSchema_GREEN := MATCH ∧ Deterministic ∧ IndependentOracleGREEN ∧ CrossAgreementGREEN ∧ EvidenceBound`

`W3.1_GREEN = CI_GREEN ∧ Oracle_GREEN ∧ Reproduction_GREEN ∧ IndependentPG_GREEN ∧ ActualSchema_GREEN ∧ Evidence_RECONCILED`

W3.1 GREEN remains bounded to PostgreSQL versions, schema classes, canonicalization rules, runtime and declared domain actually tested.

This contract does not authorize production implementation; it defines the falsifiable assurance target.
