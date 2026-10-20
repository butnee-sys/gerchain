# EA-35 Migration Recurrence: Root-Cause Analysis and Repair Plan

Status: INVESTIGATION / NOT LOCKED
Scope: PostgreSQL migration concurrency, checksum immutability, idempotency, fresh production boot.
Branch baseline inspected: `feat/ea21-transaction-aware-ledger`
Inspected source: `postgres/migrations.py`, `postgres/schema/001_concurrency.sql`, `tests/postgres/test_migrations.py`.

## 1. Observed facts

1. The migration runner now requests a PostgreSQL session-level advisory lock using `pg_advisory_lock(MIGRATION_LOCK_KEY)` and explicitly unlocks it in `finally`.
2. The runner creates `schema_version`, obtains `LOCK TABLE schema_version IN ACCESS EXCLUSIVE MODE`, checks duplicate/conflicting historical rows, and creates a unique index on `schema_version(version)`.
3. Publication uses `INSERT ... ON CONFLICT (version) DO UPDATE SET checksum = schema_version.checksum WHERE schema_version.checksum = EXCLUDED.checksum RETURNING checksum`. A checksum mismatch should return no row and raise.
4. Existing `tests/postgres/test_migrations.py` verifies canonical file selection, duplicate filename handling, checksum format, SQL splitting, and compatibility re-export. The inspected test file does **not** demonstrate two independent PostgreSQL sessions racing the same migration, checksum conflict against a live database, or fresh PostgreSQL production boot.
5. The active migration chain includes migrations 001–016. Historical aliases exist for versions 001–005, so deterministic selection and checksum history need explicit coverage.
6. Source-level guards are not runtime proof. Current exact-SHA PostgreSQL execution logs and boot evidence have not been established by this investigation.

## 2. Recurrence hypotheses to distinguish with evidence

Do not select one hypothesis until logs/test output identify it.

### H1 — Concurrency is only tested structurally, not under real parallel PostgreSQL sessions
A sequential test cannot reproduce two runners simultaneously reading/publishing migration state. If any caller bypasses the same advisory-lock protocol, only the table lock and unique index remain as backstops. The regression must use two independent connections/processes and a synchronization barrier.

### H2 — Migration work and registry publication are not one atomic unit for every supported driver/caller
The runner has transaction-state checks and strips explicit BEGIN/COMMIT tokens from migration text. Validate the actual connection type, autocommit mode, implicit transaction boundaries, exception rollback, and advisory lock lifetime in the real runner. Capture PostgreSQL `pg_locks` and `pg_stat_activity` while two runners overlap.

### H3 — Checksum history contains legacy aliases or conflicting rows
The code intentionally accepts several frozen/legacy checksums for some versions. This may be required for previously deployed databases, but it expands the set of accepted historical values. A changed migration must fail unless its exact checksum is explicitly documented as a legitimate historical alias. Do not add new aliases merely to make a failing test pass.

### H4 — A retry appears idempotent but changes schema or registry state
The current duplicate-row cleanup and unique-index creation are intentional repair operations. Therefore idempotency must be measured from a clean state after the first successful migration: compare schema catalog, registry rows/checksums, and row counts before and after the second run. Separately test a legacy duplicate-row repair path; do not confuse repair-once behavior with steady-state idempotency.

### H5 — Fresh boot exercises a different initialization path than migration tests
The production factory's `metadata.create_all` is not a substitute for the canonical SQL migration runner. The boot gate must run the numbered migrations on an empty PostgreSQL database, then construct the runtime and assert Canonical Ledger authority. If boot creates ORM tables first and migrations second, record that order and fail if it masks missing migration DDL.

## 3. Required evidence bundle

Every evidence record must include:
- exact commit SHA and branch;
- PostgreSQL server version and driver/SQLAlchemy versions;
- database reset/creation procedure;
- command/workflow run ID and timestamps;
- migration runner stdout/stderr and exit codes;
- schema_version rows before/after;
- canonical migration version + checksum list;
- `pg_locks` / `pg_stat_activity` snapshot for concurrency test;
- table/index/constraint catalog fingerprint before and after idempotency replay;
- production entrypoint exit status and `is_canonical_ledger_authoritative` assertion;
- failure reproduction and regression result.

Do not use a local SQLite test as evidence for PostgreSQL locking semantics.

## 4. Repair sequence — gates must pass in order

### Gate A — Reproduce and preserve failure evidence
1. Run current branch on a disposable PostgreSQL database with two independent runner sessions released from a barrier.
2. Save logs and registry/catalog snapshots before any code change.
3. Re-run the exact failing scenario three times to check whether the failure is deterministic or timing-dependent.
4. Classify the result: duplicate version rows, duplicate-key error, checksum mismatch, DDL collision, lock timeout/deadlock, or boot failure.

### Gate B — Migration concurrency serialization
1. Confirm the session-level advisory lock is acquired before registry inspection and held until all DDL plus registry publication completes.
2. Confirm every supported entrypoint calls the same canonical runner and uses the same lock key/database.
3. Use two independent PostgreSQL connections. Assert one migration body executes once, one registry row exists per version, both callers terminate successfully or one waits and safely no-ops.
4. Add timeout and exception-path assertions: rollback occurs, advisory lock is released, and a subsequent runner succeeds.
5. Inspect lock state while the first runner is paused and the second is waiting.

### Gate C — Checksum conflict is fail-closed
1. Apply a migration and record its checksum.
2. Change the content for the same version in an isolated temporary migration directory.
3. Re-run and assert an explicit checksum-mismatch exception, non-zero exit, and no schema_version rewrite.
4. Verify conflict detection for pre-existing duplicate rows with different checksums.
5. Test only approved frozen/legacy checksum aliases; do not broaden the allowlist to suppress a failure.

### Gate D — Idempotency
1. Apply all migrations to a fresh database.
2. Snapshot registry rows/checksums, relevant table/index/constraint definitions, and row counts.
3. Run the same migration set again.
4. Assert registry and schema snapshots are byte-for-byte/logically identical and no migration body is re-applied.
5. Test legacy identical duplicate-row repair separately; assert conflicting duplicates fail before cleanup.

### Gate E — Fresh PostgreSQL boot
1. Provision an empty disposable PostgreSQL database.
2. Run the canonical migration runner only; verify versions 001–016 and checksums.
3. Verify required canonical Ledger, Escrow, Witness, Outbox, and durable idempotency tables/constraints exist.
4. Construct the production runtime from the exact production factory/entrypoint path.
5. Assert PostgreSQL dialect, Canonical Ledger authority, and no silent fallback to MoneyLedger, ReleaseAccount, AccountBalance, or SQLite.
6. Run a minimal non-value-mutating health/readiness check; do not invent escrow/account seed data unless the boot contract explicitly requires it.
7. Run a transactional smoke test and verify rollback leaves no partial movement, witness, outbox, or idempotency record.

### Gate F — Exact-SHA re-performance
1. Commit fixes and tests.
2. Trigger CI on that exact SHA.
3. Confirm PostgreSQL concurrency, checksum conflict, idempotency, fresh migration, and production boot jobs all executed—not merely queued or skipped.
4. Preserve workflow run/job IDs and logs.
5. Re-run once on the same SHA after any fix. Any subsequent commit invalidates the evidence.
6. Mark GREEN only if all gates pass with evidence; otherwise retain IN PROGRESS / NOT LOCKED.

## 5. Exit criteria

- No duplicate schema_version rows; unique version index/constraint is valid.
- Concurrent runners cannot execute/publish the same migration twice.
- Same version with an unapproved different checksum fails closed and does not rewrite history.
- Reapplying migrations leaves schema and registry unchanged.
- Fresh PostgreSQL migrations and production runtime boot succeed on the exact SHA.
- CI logs prove each required gate ran.
- No unexplained checksum aliases or silent compatibility fallback.
