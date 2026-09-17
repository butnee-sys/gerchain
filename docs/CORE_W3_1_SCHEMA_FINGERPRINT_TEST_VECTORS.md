# CORE W3.1 — Canonical Schema Fingerprint Test Vectors v1.1

## Status

Assurance test-vector specification for the bounded W3.1 logical PostgreSQL schema domain.

## 1. Identity separation

Three identities remain distinct:

`MigrationIdentity = (MigrationID, SchemaID, FromVersion, ToVersion, MigrationHash)`

`RecordedSchemaIdentity = (SchemaID, Version, DescriptorVersion, StateHash)`

`PhysicalSchemaFingerprint = SHA256(CanonicalSerialize(LogicalSchema))`

Therefore:

`MigrationHash != PhysicalSchemaFingerprint`

and:

`AuthorityIdentity != PhysicalSchemaFingerprint`

## 2. Validated domain

v1.1 includes:

`TABLE, COLUMN, TYPE, NULLABILITY, DEFAULT, PRIMARY KEY, UNIQUE, CHECK, FOREIGN KEY, STANDARD STANDALONE INDEX`

Out of domain unless explicitly added by a later descriptor version:

`TRIGGER, VIEW, MATERIALIZED VIEW, FUNCTION, PROCEDURE, SEQUENCE, EXTENSION, PARTITIONING, RLS POLICY, EXPRESSION INDEX, PARTIAL INDEX, CUSTOM OPERATOR CLASS, ADVANCED INDEX OPTIONS`

## 3. Canonical logical descriptor

`LogicalSchema = Projection(PostgreSQLCatalog, DeclaredScope)`

`Table = (Namespace, Name, Columns, PrimaryKeys, UniqueConstraints, Checks, ForeignKeys)`

`Column = (Ordinal, Name, Type, Nullable, DefaultExpression)`

`Type = (TypeSchema, TypeName, Parameters, ArrayDimensions)`

`PK/UNIQUE/FK` preserve declared composite column order.

`Index = (Namespace, Name, Table, Unique, Method, KeyColumns, IncludedColumns)` for standard column indexes.

PK/UNIQUE backing indexes are implementation artifacts and are excluded from standalone index semantics.

## 4. Canonicalization rules

1. UTF-8 deterministic serialization.
2. PostgreSQL-resolved identifier identity.
3. Independent collections sorted deterministically.
4. Column ordinals preserved.
5. Composite key order preserved.
6. Explicit null representation.
7. Descriptor serialization versioned.
8. Physical IDs, timestamps, PIDs and transaction IDs excluded.
9. Bounded type representation normalized deterministically.
10. Default/check expression normalization is limited to the supported PostgreSQL semantic representation; unsupported forms are OUT_OF_DOMAIN.

## 5. Vector A — baseline

```text
core.accounts
  id         bigint NOT NULL
  owner_id   text   NOT NULL
  balance    bigint NOT NULL
  PRIMARY KEY (id)
```

A establishes the baseline fingerprint.

A primary-key backing index is NOT a standalone secondary index for this descriptor.

## 6. Vector B — additive column

Add:

`status text NOT NULL DEFAULT 'ACTIVE'`

Required:

`Fingerprint(B) != Fingerprint(A)`

## 7. Vector C — nullability mutation

Change `balance bigint NOT NULL` to `balance bigint NULL`.

Required:

`Fingerprint(C) != Fingerprint(A)`

## 8. Vector D — type mutation

Change the type of `balance` while retaining the same column identity.

Required:

`Fingerprint(D) != Fingerprint(A)`

## 9. Vector E1 — primary-key mutation

Change PK membership or ordered composite PK definition.

Required:

`Fingerprint(E1) != Fingerprint(A)`

## 10. Vector E2 — UNIQUE mutation

Add or mutate a UNIQUE constraint.

Required:

`Fingerprint(E2) != Fingerprint(A)`

## 11. Vector E3 — CHECK mutation

Add or mutate a CHECK constraint.

Required:

`Fingerprint(E3) != Fingerprint(A)`

## 12. Vector E4 — FOREIGN KEY mutation

Add or mutate a foreign key, including target or action.

Required:

`Fingerprint(E4) != Fingerprint(A)`

## 13. Vector E5 — standalone index mutation

Add or mutate a standard standalone column index.

Required:

`Fingerprint(E5) != Fingerprint(A)`

Constraint-backed indexes must not create an additional semantic difference when the corresponding PK/UNIQUE constraint is unchanged.

## 14. Vector F — representation/order invariance

Create the same logical schema through different DDL/catalog insertion orders.

Required:

`Fingerprint(F1) == Fingerprint(F2)`

## 15. Vector G — scope isolation

Add an explicitly out-of-domain object.

Required:

`Fingerprint(G) == Fingerprint(A)`

provided the object is genuinely outside the declared v1.1 scope.

## 16. Vector H — recorded mismatch

Recorded hash = `Fingerprint(A)` while actual schema = B.

Required:

`RECONCILIATION = RECORDED_MISMATCH`

No repair is permitted.

## 17. Vector I — version deception

Recorded and actual authority version numbers appear equal while physical fingerprints differ.

Required:

`RECONCILIATION != MATCH`

Version equality cannot mask structural mismatch.

## 18. Vector J — authority deception

Actual physical schema equals the expected fingerprint, but the migration identity/predecessor is invalid.

Required:

`AUTHORITY_VALID = false`

and W3.1 assurance remains non-GREEN.

## 19. Vector K — fresh-process determinism

Independent processes A, B and C calculate the same descriptor/fingerprint from the same schema facts.

Required:

`Descriptor_A == Descriptor_B == Descriptor_C`

and:

`Fingerprint_A == Fingerprint_B == Fingerprint_C`

## 20. Cross-agreement

The independent oracle and PostgreSQL observer must independently produce the same canonical descriptor and fingerprint:

`Descriptor_oracle == Descriptor_observer`

`Fingerprint_oracle == Fingerprint_observer`

Any disagreement is non-GREEN.

## 21. Closure

`W3.1-A_GREEN = ContractFrozen ∧ OraclePASS ∧ ObserverPASS ∧ A-KPASS ∧ CrossAgreementPASS ∧ FreshProcessPASS ∧ IndependentPGPASS ∧ EvidenceBound ∧ EvidenceReconciled`

W3.1-B production migration execution remains blocked until W3.1-A is GREEN.
