# CORE W3.1 — Independent Oracle Re-performance Protocol

## Status

Documentation and assurance protocol. This does not modify production source code.

## Objective

Provide a reproducible procedure by which an independent implementation can falsify the W3.1 production schema-reconciliation result using PostgreSQL catalog observations.

## Re-performance separation

The reproduction must use:

- a separate Python module or standalone script;
- direct PostgreSQL catalog queries;
- standard hashing/serialization primitives;
- no import from GerChain production persistence or reconciliation modules.

The reproduction must not call the production fingerprint function and must not compare only the production output to itself.

## Environment identity

Record:

- Python version
- operating system and architecture
- PostgreSQL major version
- PostgreSQL server version
- client driver/version
- repository commit under test
- oracle implementation hash
- descriptor version
- declared schema scope
- test database identifier

## Procedure

### Phase 1 — baseline

1. Create an isolated PostgreSQL database.
2. Create the declared baseline schema.
3. Query PostgreSQL catalogs independently.
4. Build the canonical descriptor.
5. Calculate SHA-256.
6. Store the observed descriptor and fingerprint as evidence.

Expected: deterministic baseline fingerprint.

### Phase 2 — semantic mutations

Apply one mutation at a time:

1. add column;
2. change nullability;
3. change data type;
4. add/remove constraint;
5. add/remove index;
6. add/remove foreign key;
7. change default expression.

For each mutation:

`Fingerprint_after != Fingerprint_before`

unless the mutation is explicitly outside the declared schema scope.

### Phase 3 — representation invariance

Construct the same logical schema through different DDL orderings.

Expected:

`Fingerprint_A == Fingerprint_B`

This specifically falsifies catalog-order dependence.

### Phase 4 — scope boundary

Add an explicitly out-of-scope object.

Expected:

`Fingerprint_with_out_of_scope == Fingerprint_without_out_of_scope`

Only if the object is genuinely excluded by the declared scope.

### Phase 5 — mismatch detection

Pair a recorded baseline fingerprint with a mutated actual schema.

Expected:

`MATCH = false`

No repair operation is permitted.

### Phase 6 — authority separation

Use an actual schema whose physical fingerprint matches the expected schema but provide an invalid migration identity or predecessor.

Expected:

physical reconciliation may be true, but W3/W3.1 authority validation remains false.

This proves that physical schema matching cannot substitute for migration authority.

### Phase 7 — deterministic replay

Repeat the entire catalog observation and fingerprint process in fresh processes.

Expected:

all canonical descriptors and fingerprints are byte-identical.

## Required outputs

Each run must produce machine-readable evidence containing:

`run_id`

`commit`

`runtime`

`postgres_version`

`descriptor_version`

`declared_scope`

`canonical_descriptor`

`actual_fingerprint`

`recorded_hash`

`verdict`

`oracle_version`

`evidence_hash`

## Falsification criteria

The re-performance fails if any of the following occurs:

- identical logical schemas produce different fingerprints;
- semantic schema mutations produce the same fingerprint;
- catalog ordering changes the fingerprint;
- an in-scope object is silently ignored;
- an out-of-scope object changes the fingerprint without scope declaration;
- mismatch is not detected;
- oracle and production reconciler disagree;
- repeated runs differ;
- authority and physical reconciliation are conflated;
- evidence cannot be bound to the exact runtime and commit.

## Closure

`IndependentReproduction_GREEN := PostgreSQLObserved ∧ IndependentCanonicalization ∧ Deterministic ∧ MutationSensitive ∧ OrderingInvariant ∧ ScopeBound ∧ EvidenceBound`

This protocol establishes the test procedure only. It does not constitute execution evidence and therefore cannot itself make W3.1 GREEN.
