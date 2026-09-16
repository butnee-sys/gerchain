# CORE W3.1 — Independent Schema Reconciliation Oracle Contract

## Status

Assurance contract only. No production source code is modified by this document.

## 1. Objective

The independent oracle determines whether an observed PostgreSQL schema is structurally identical to the schema represented by the recorded W3/W3.1 authority state.

The oracle must be capable of falsifying the production reconciler. It must not reproduce the production implementation by importing or calling it.

## 2. Independence boundary

The oracle MUST NOT import:

- `persistence.schema_authority`
- the W3.1 migration executor
- the production schema reconciler
- production fingerprint functions
- production migration state-transition functions

The oracle MAY consume the public W3.1 contract and independently query PostgreSQL catalog metadata.

## 3. Oracle input

The oracle receives:

`O = (SchemaID, ExpectedVersion, DeclaredScope, RecordedStateHash, DescriptorVersion, PostgreSQLConnection)`

The PostgreSQL connection is read-only for oracle execution.

The oracle must never execute DDL, mutate authority state, repair mismatches, or update evidence records.

## 4. Independent derivation

The oracle independently derives:

`ASD_o = CanonicalDescriptor(PostgreSQLCatalog, DeclaredScope)`

and then:

`F_o = SHA256(CanonicalSerialize_o(ASD_o))`

The oracle verdict is:

`MATCH_o := RecordedStateHash == F_o`

subject to schema identity, descriptor version, expected version, and scope checks.

## 5. Required agreement

Production reconciler and independent oracle must agree on:

- object inclusion;
- object identity;
- column semantics;
- constraint semantics;
- index semantics;
- foreign-key semantics;
- canonical ordering;
- null representation;
- normalized expression representation;
- descriptor version;
- fingerprint algorithm.

They must NOT agree merely because they share implementation code.

## 6. Required oracle test vectors

The oracle must independently evaluate all vectors in:

`docs/CORE_W3_1_SCHEMA_FINGERPRINT_TEST_VECTORS.md`

Minimum assertions:

1. identical schema → identical fingerprint;
2. added column → different fingerprint;
3. nullability change → different fingerprint;
4. constraint change → different fingerprint;
5. index change → different fingerprint;
6. catalog ordering variation → same fingerprint;
7. declared out-of-scope object → unchanged fingerprint;
8. recorded/actual mismatch → RED;
9. version equality alone → insufficient;
10. correct physical schema with wrong authority identity → RED;
11. repeated independent execution → byte-identical output.

## 7. Cross-implementation falsification

At least two implementations must exist:

`Implementation A = production reconciliation path`

`Implementation B = independent oracle`

For every valid test vector:

`Verdict_A == Verdict_B`

and, where fingerprints are in scope:

`Fingerprint_A == Fingerprint_B`

Any disagreement is an assurance failure, not an averaging opportunity.

## 8. Adversarial cases

The oracle must cover:

- reordered catalog rows;
- reordered unordered constraint members;
- changed ordered index keys;
- changed type;
- changed nullability;
- changed default expression;
- added/removed constraints;
- added/removed indexes;
- added/removed foreign keys;
- unauthorized objects;
- wrong schema namespace;
- wrong SchemaID;
- wrong descriptor version;
- recorded hash mismatch;
- repeated execution;
- inspection failure.

## 9. Failure semantics

The following are not GREEN:

`OracleMismatch`

`InspectionError`

`ScopeError`

`IdentityMismatch`

`DescriptorVersionMismatch`

`RecordedHashMismatch`

`Undetermined`

An unknown oracle result is `INCONCLUSIVE`, never GREEN.

## 10. Evidence identity

Each oracle run must record at minimum:

`OracleEvidence = (GateID, RunID, Commit, SchemaID, ExpectedVersion, DeclaredScope, DescriptorVersion, ActualFingerprint, RecordedHash, Verdict, RuntimeFingerprint, Timestamp, EvidenceHash)`

The evidence must bind to the exact tested commit and runtime.

## 11. Independent PostgreSQL reproduction

A separate reproduction must execute against PostgreSQL without importing Gerchain production modules.

It must demonstrate at minimum:

- actual catalog inspection;
- deterministic descriptor generation;
- deterministic fingerprinting;
- mismatch detection;
- ordering invariance;
- structural mutation detection.

The reproduction is evidence of the contract, not proof of all production behavior.

## 12. Closure predicate

`ORACLE_GREEN := IndependentImplementation ∧ IndependentPostgreSQL ∧ VectorSuitePASS ∧ DeterministicReplay ∧ EvidenceBound`

W3.1 remains OPEN until the migration executor, actual-schema reconciliation, oracle, PostgreSQL reproduction, and evidence reconciliation are all closed.

## 13. Authority separation

The oracle observes. It does not authorize.

`Authority → Schema Authority`

`Execution → Migration Executor`

`Observation → Actual Schema Reconciler`

`Falsification → Independent Oracle`

No layer may silently assume another layer's authority.
