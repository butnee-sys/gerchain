# PostgreSQL Migration Isolation and Concurrency Verification

Status: IMPLEMENTATION SPECIFICATION — NOT EXECUTED / NOT VERIFIED

## Safety boundary

The integration test MUST require `GERCHAIN_TEST_DATABASE_URL`. If it is unset, mark the PostgreSQL verification as SKIPPED/UNVERIFIED; never report success. The test must connect only to a dedicated test database and create two unique temporary schemas per run. It must not create, alter, truncate, or drop objects in the database's default/application schema.

Schema A is the legacy-data fixture and migration target. Schema B is the isolated control/reference schema used to verify the runner's migration ledger and concurrency behavior. Set each connection's PostgreSQL `search_path` explicitly; do not rely on a shared default search_path.

## Required evidence

1. Seed representative legacy escrow rows in Schema A, including IDs, sender_address, refund_destination, currency, state, amount, condition, and timestamps where present.
2. Capture a deterministic, ordered pre-migration snapshot of all business fields. Keep structural fields that legitimately require backfill (for example created_at when the legacy schema lacks it) separately from business fields.
3. Run all 16 repository migrations against Schema A. Assert business-field equality against the snapshot. Assert every required structural backfill is non-null and satisfies the migration's documented rule. Do not invent a timestamp rule: it must match the migration contract.
4. Run two independent migration runners concurrently against the same target schema. Assert each migration version has exactly one ledger row; checksum and applied_at remain unchanged after a second no-op run; the final ledger contains the expected 16 versions. Use transaction/advisory locking appropriate to the actual runner. The test must fail if runner concurrency is not serialized.
5. Emit a machine-readable result containing repository, branch, exact commit SHA, PostgreSQL server version, migration count, both schema names, snapshot digest, checksums, runner exit codes, and pass/fail outcomes.

## Acceptance criteria

- No writes outside the two test schemas.
- No business-value changes after migration.
- Exactly 16 unique applied migration versions.
- Two concurrent runners converge on one identical migration ledger.
- Re-running migrations is idempotent: checksum and applied_at do not change.
- Results are bound to the exact commit SHA tested.

## Important limitation

This specification is not evidence of a successful run. Before implementation, the repository's actual migration runner, migration directory, ledger schema, and timestamp backfill rule must be identified and wired into the harness. If `GERCHAIN_TEST_DATABASE_URL` is absent or PostgreSQL cannot be reached, status remains UNVERIFIED.
