# PostgreSQL Migration Incident Assessment — Schema Version Race and Escrow State Check

Status: **IMPLEMENTED GUARDRAILS / PRODUCTION RE-PERFORMANCE REQUIRED / NOT FINAL-LOCKED**

## Scope

This record assesses two PostgreSQL log observations:

1. A duplicate-key violation for `schema_version.version = 2`.
2. A `CHECK` violation for escrow state `NOT_A_STATE` against `escrows_state_check`.

These observations have different meanings and must not be grouped as one failure.

## Finding 1 — Duplicate schema version publication

### Interpretation

A duplicate-key violation means at least two writers attempted to publish the same version key without a serialization/idempotency path that successfully coordinated them, or a legacy bootstrap path bypassed the canonical migration runner. It does **not**, by itself, prove that migration DDL was partially applied or that the schema is corrupt. The transaction outcome and final migration ledger must be inspected.

### Canonical safeguards in the current migration runner

`postgres/migrations/__init__.py` currently:

- acquires a PostgreSQL session-level advisory lock before registry work;
- runs DDL and version publication in a transaction;
- checks and rejects conflicting checksums for one version;
- collapses identical duplicate legacy publications before enforcing uniqueness;
- establishes a unique index on `schema_version(version)` if no qualifying single-column unique key exists;
- publishes versions with `INSERT ... ON CONFLICT (version) DO NOTHING`;
- re-reads the published checksum and fails closed if it does not match the accepted checksum;
- releases the advisory lock on both success and failure.

The production runtime factory calls this canonical runner before asserting the canonical schema. This is the intended single serialization path.

### Remaining forensic requirement

The historical log entry alone cannot establish whether it came from the current runner, an older build, a separate migration process, or direct SQL. Before closing this finding, record:

- exact failing commit/image digest and migration command;
- SQLSTATE and full constraint/index name;
- concurrent process/job identities and timestamps;
- whether the failed statement's transaction rolled back;
- final `schema_version` rows, checksums, and unique-key definition;
- exact-commit rerun result with two simultaneous migration connections.

Do not suppress duplicate-key errors globally. The runner must remain fail-closed on checksum disagreement or schema drift.

## Finding 2 — Rejection of `NOT_A_STATE`

### Interpretation

A `CHECK` violation for `NOT_A_STATE` is the expected result of a negative test if the test deliberately inserts an invalid state. It is not a product defect solely because PostgreSQL logs the rejected statement.

The current canonical regression test `tests/postgres/test_migration_concurrency.py::test_invalid_escrow_state_is_rejected_by_named_database_constraint` explicitly expects `psycopg.errors.CheckViolation` and asserts that the constraint name is `escrows_state_canonical_check`.

### Required test semantics

- Expected exception: catch and assert the exact PostgreSQL check violation.
- Expected constraint: `escrows_state_canonical_check`.
- Expected postcondition: the invalid row is not committed.
- Any unhandled exception, wrong constraint, or committed invalid row is a test failure.
- An unexpected production request containing `NOT_A_STATE` must be rejected; it must not be normalized or silently accepted.

The legacy name `escrows_state_check` in the log is a clue to verify the exact database/schema/build under test. The canonical migration chain versions 014–016 reconciles state-check drift and asserts that exactly one validated canonical state constraint remains. Do not infer that the live database has been repaired until the exact target database has been inspected after migration.

## Required proof gates before FINAL LOCK

1. Run the full canonical migration chain on a clean, disposable PostgreSQL database at the candidate commit.
2. Run the two-connection migration race test; prove exactly one process applies versions 1–16 and the other observes them as already applied.
3. Verify exactly 16 unique version rows, non-empty checksums, and one unique key on `schema_version.version`.
4. Re-run migration and prove version/checksum/timestamp rows are unchanged.
5. Run the invalid-state negative test and prove the exact canonical constraint rejects the row.
6. Inspect the target database after migration: exactly one validated escrow-state CHECK named `escrows_state_canonical_check`.
7. Capture exact commit SHA, PostgreSQL version, test command, exit status, and logs/artifacts.
8. Confirm all other required production gates and independent re-performance are complete.

## Decision

- Duplicate version publication: **guarded in canonical runner; root cause of historical log remains unproven until exact-run evidence is captured**.
- Invalid-state CHECK rejection: **expected negative-test behavior when asserted by the test; not a failure by itself**.
- Overall migration/production status: **IN PROGRESS / NOT LOCKED** until the gates above pass on the exact candidate commit and target PostgreSQL environment.
