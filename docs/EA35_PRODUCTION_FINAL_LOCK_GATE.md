# EA-35 Production Final Lock Gate

Status: **IN PROGRESS / NOT LOCKED**

This gate is intentionally not a declaration of production readiness. It defines the evidence required before the canonical architecture and EAI can be final-locked.

## Required same-commit evidence

1. Exact commit SHA and GitHub Actions run URL.
2. Fresh PostgreSQL 16 database created from an empty database.
3. Canonical migration inventory: ordered version, filename, SHA-256, applied checksum, and applied timestamp.
4. Migration idempotency: second run applies no new migrations and does not alter history.
5. Concurrency: two independent PostgreSQL sessions serialize migration application and leave one authoritative row per version.
6. Schema assertions: required tables, columns, unique constraints, and exactly one validated canonical escrow state constraint.
7. ProductionRuntimeFactory boots against the same database and establishes Canonical Ledger authority without legacy Release authority.
8. Production entrypoint starts successfully using the same canonical database URL.
9. PostgreSQL escrow lifecycle evidence for CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL, settlement and canonical reads.
10. Deep value-truth reconciliation reports no issues after lifecycle tests and after restart/recovery checks.
11. Full relevant CI jobs succeed on the exact same commit SHA; artifacts and job logs are retained and linked.
12. Independent re-performance reproduces the migration and runtime results.

## Current evidence and blockers

- A previously inspected commit had successful Snyk, CORE Operating Reconciliation, and CodeQL checks.
- That same inspected commit also had failed PostgreSQL Concurrency and core-gates runs. The logs showed a duplicate schema_version publication during the migration concurrency test, and a Python syntax error in services/gerchain_runtime.py during test collection.
- These are historical results for that inspected commit, not proof of the current branch tip's status. A fresh exact-SHA run is required after the current fixes.
- A factory-level PostgreSQL test exists and expects migration versions 1 through 17, but the existence of a test is not execution evidence.
- schema_version rows and migration checksums must be captured from the live disposable PostgreSQL database. Source inventory alone is insufficient.
- No claim of a clean PostgreSQL 16 migration, successful production entrypoint boot, full lifecycle, zero-issue deep reconciliation, or independent re-performance is made by this document.

## Final lock rule

Do not set this gate to PASS and do not declare PRODUCTION READY until every required item above has an attached, reproducible artifact tied to the same exact commit SHA. Any missing, stale, failed, or ambiguous evidence keeps the gate **IN PROGRESS / NOT LOCKED**.

## Evidence report contract

The CI artifact should include:
- commit SHA and UTC timestamp;
- PostgreSQL server version and database identity (no credentials);
- ordered migration version/name/SHA-256 inventory;
- applied schema_version version/checksum/timestamp rows;
- first-run and second-run history equality;
- required schema/table/constraint assertions;
- entrypoint boot and readiness result;
- lifecycle operation results;
- deep reconciliation issue list;
- exact workflow/run/job URLs and final conclusions.
