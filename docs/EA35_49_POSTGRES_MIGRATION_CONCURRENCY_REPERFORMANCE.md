# EA-35.49 — PostgreSQL Migration Concurrency Re-performance

Status: **OPEN / NOT VERIFIED / NOT LOCKED**

Target branch: `feat/ea21-transaction-aware-ledger`

This record defines the exact acceptance gate. It is not evidence that the tests have run.

## Required evidence identity

Every run must record:
- exact tested Git commit SHA (the workflow must assert it matches `GITHUB_SHA`);
- PostgreSQL server version (`SHOW server_version`);
- Python and migration-driver versions;
- migration file path and SHA-256 checksum;
- both runner process exit codes and timestamped logs;
- resulting `schema_version` rows and relevant schema catalog state.

## Required concurrency scenarios

1. **Concurrent first application:** start two independent runner processes against the same empty disposable PostgreSQL database, release them from a synchronization barrier, and apply the same migration. Exactly one version row must exist; both processes must finish deterministically (one applies, the other observes the applied checksum).
2. **Same-checksum replay:** reapply the same migration; succeed without duplicate DDL effects or a duplicate version row.
3. **Checksum conflict:** change the migration bytes while keeping the version identifier fixed; fail closed and leave the prior checksum unchanged.
4. **Atomic failure:** run a deliberately failing migration inside a transaction; verify no migration version row and no partial transactional DDL/data effects remain.
5. **Serialization:** runner must use a PostgreSQL transaction-scoped advisory lock (or an equivalent row-lock protocol that is created safely under concurrent first use), and re-check migration state after obtaining the lock. Do not rely on a process-local lock.
6. **Clean repeat:** run the complete migration set twice against a fresh database and confirm the second run is an idempotent no-op.

## Pass criteria

- All scenarios pass on the same exact commit SHA.
- No duplicate version, checksum drift, partial failed migration, or ambiguous runner outcome.
- Logs and version output are attached as a workflow artifact.
- The test uses PostgreSQL, not SQLite or mocked sessions.

## Current known risk

`postgres/schema/001_concurrency.sql` declares `schema_version(version, checksum, applied_at)`, but a schema table alone does not prove that a migration runner serializes concurrent processes or applies the migration and version record atomically. Existing source inspection is not a substitute for PostgreSQL execution.

## Lock decision

Do not mark EA-35.49 GREEN until exact-SHA PostgreSQL workflow evidence and logs are inspected. Until then: **OPEN / NOT VERIFIED / NOT LOCKED**.
