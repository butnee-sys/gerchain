# CORE W3.1 — Actual PostgreSQL Schema Reconciliation Contract

## 1. Purpose

This contract defines how recorded CORE schema authority is compared with the actual PostgreSQL schema. It does not execute DDL and does not grant reconciliation any authority to mutate the database.

CORE schema truth is the conjunction of:

`RecordedAuthorityState ∧ ActualSchemaDescriptor`

A schema version number alone is insufficient evidence of physical schema state.

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

## 3. Canonical actual-schema descriptor

For a declared CORE schema scope, the reconciler constructs:

`ASD = (SchemaID, Objects, Constraints, Indexes, ForeignKeys, Extensions, DescriptorVersion)`

Only explicitly declared authoritative object classes are included. Objects outside the declared scope are not silently included in the fingerprint.

### 3.1 Object identity

Each authoritative object is represented canonically by:

`Object = (Kind, Namespace, Name, Definition)`

Definitions MUST be normalized deterministically before hashing.

### 3.2 Table representation

A table descriptor includes, at minimum:

`Table = (Namespace, Name, Columns, PrimaryKey, UniqueConstraints, ForeignKeys, Checks)`

Each column includes:

`Column = (Ordinal, Name, Type, Nullable, DefaultExpression)`

Only semantics declared authoritative by the schema contract are included. Formatting differences that do not change PostgreSQL semantics MUST NOT change the fingerprint.

### 3.3 Index representation

`Index = (Namespace, Name, Table, Unique, Method, Definition)`

Indexes are ordered canonically by namespace, table, and name.

### 3.4 Foreign-key representation

`ForeignKey = (Table, Name, Columns, ReferencedTable, ReferencedColumns, OnUpdate, OnDelete)`

### 3.5 Extensions and schema-level objects

Extensions or other PostgreSQL objects are included only when explicitly declared part of the authoritative CORE schema domain. Their inclusion policy MUST be versioned as part of the descriptor contract.

## 4. Fingerprint

The actual schema fingerprint is:

`ActualSchemaFingerprint = SHA256(CanonicalSerialize(ASD))`

Canonical serialization MUST use deterministic ordering and explicit field encoding.

The recorded schema state contains the corresponding expected state hash:

`RecordedStateHash`

Reconciliation predicate:

`RECONCILED := RecordedStateHash == ActualSchemaFingerprint`

Subject to the same SchemaID, descriptor version, and declared scope.

## 5. Migration hash versus schema-state hash

These are different identities.

### MigrationHash

Identifies the declared migration definition/DDL payload:

`MigrationHash = Hash(MigrationDefinition)`

### ActualSchemaFingerprint

Identifies the resulting physical schema:

`ActualSchemaFingerprint = Hash(ActualSchemaDescriptor)`

Therefore:

`MigrationHash ≠ ActualSchemaFingerprint`

A migration may have a valid migration hash while producing an unexpected actual schema. Conversely, an actual schema may match an expected fingerprint while the migration identity is unauthorized. Both dimensions must be checked.

## 6. Reconciliation states

The reconciler returns one of:

- `MATCH` — recorded authority and actual schema agree within the declared descriptor scope.
- `RECORDED_MISMATCH` — recorded schema state exists but actual schema differs.
- `ACTUAL_UNEXPECTED` — actual authoritative objects exist without a matching recorded authority state.
- `RECORDED_MISSING` — authority expects objects/structure that are absent.
- `IDENTITY_MISMATCH` — SchemaID or descriptor identity does not match.
- `SCOPE_ERROR` — required schema objects cannot be classified under the declared scope.
- `INSPECTION_ERROR` — actual schema could not be reliably observed.

`MATCH` is required for W3.1 GREEN.

All other states are non-GREEN until independently reconciled.

## 7. Critical mismatch rule

Examples:

`Recorded = V8 / Hash A`
`Actual   = V8 / Hash B`

→ `RECORDED_MISMATCH`

`Recorded = V8`
`Actual   = V7`

→ `RECORDED_MISMATCH`

`Recorded = V8 / Hash A`
`Actual contains unauthorized table`

→ `ACTUAL_UNEXPECTED`

A numeric version match MUST NOT mask a structural mismatch.

## 8. Atomic migration expectation

For migrations compatible with PostgreSQL transactional DDL, the intended boundary is:

`BEGIN → Authority Lock → Predecessor Validation → DDL → Actual Schema Verification → Authority Commit → COMMIT`

If verification fails, the transaction MUST NOT publish the successor authority.

For operations that cannot participate safely in one transaction, a separate recovery contract is mandatory. They MUST NOT be presented as atomic merely because an application-level transaction exists.

## 9. Reader safety

During an uncommitted migration, readers must not observe a committed successor authority state.

The assurance requirement is:

`VisibleAuthorityState ∈ CommittedStates`

A reader observing an old committed state during an in-progress migration is acceptable. A reader observing a false or partially committed successor is not.

## 10. Falsification cases

The reconciliation implementation must eventually test at least:

1. exact schema match;
2. column added;
3. column removed;
4. column type changed;
5. nullability changed;
6. constraint changed;
7. index changed;
8. foreign-key changed;
9. unauthorized object added;
10. recorded version ahead of actual schema;
11. actual schema ahead of recorded authority;
12. same version with different structural hash;
13. deterministic repeated fingerprinting;
14. reader during uncommitted DDL;
15. rollback after failed DDL;
16. committed retry with unchanged schema;
17. inspection failure;
18. descriptor-scope violation.

## 11. Independent oracle

The independent oracle must derive the expected semantic descriptor without importing CORE production reconciliation code.

It must independently verify:

`CanonicalDescriptor → ExpectedFingerprint → Comparison → Verdict`

The independent oracle MUST reproduce at least the mismatch classes and deterministic fingerprint property.

## 12. Evidence identity

Every reconciliation run must bind:

`(EvidenceID, GateID, RunID, Commit, SchemaID, AuthorityVersion, DescriptorVersion, DeclaredScope, ActualFingerprint, RecordedHash, OracleVersion, RuntimeFingerprint, Timestamp, Verdict, EvidenceHash)`

No reconciliation evidence without these identity fields may support W3.1 GREEN.

## 13. Closure condition

`ActualSchema_GREEN := MATCH ∧ Deterministic ∧ IndependentOracleGREEN ∧ EvidenceBound`

and:

`W3.1_GREEN = CI_GREEN ∧ Oracle_GREEN ∧ Reproduction_GREEN ∧ IndependentPG_GREEN ∧ ActualSchema_GREEN ∧ Evidence_RECONCILED`

This contract does not authorize production implementation. It defines the falsifiable assurance target for the subsequent implementation work.
