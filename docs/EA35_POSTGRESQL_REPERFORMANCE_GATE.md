# EA-35 PostgreSQL Re-performance Gate

Status: **IN PROGRESS / NOT LOCKED**

This gate is evidence-driven. A source review or a successful unit-test run is not proof that a clean PostgreSQL migration and production boot have succeeded.

## Required execution environment

- Disposable PostgreSQL 16 database.
- `GERCHAIN_POSTGRES_DSN` pointing to the disposable database.
- The exact Git commit under review checked out in the runner.
- Preserve workflow run ID, job ID, commit SHA, migration output, and final catalog query output together.

## Required order

1. Create a genuinely empty disposable database.
2. Apply the canonical migrations once.
3. Capture `schema_version` as ordered `(version, checksum)` pairs.
4. Verify versions are unique, contiguous from 1 through the expected latest version, and each checksum is non-empty.
5. Re-run the complete migration set.
6. Assert the ordered version/checksum pairs are byte-for-byte unchanged.
7. Query PostgreSQL catalogs for required tables, columns, constraints, and unique indexes.
8. Boot `production_entrypoint.py` using the same PostgreSQL database and verify the runtime selected Canonical Ledger authority.
9. Execute the required escrow lifecycle and deep value-truth reconciliation in an isolated integration test.
10. Restart/recovery test and verify no duplicate value movement.
11. Attach all results to the exact commit SHA. A workflow run on an earlier SHA is historical evidence only.

## Fail-closed rules

- Duplicate `schema_version.version` publication is a failure, not a warning.
- Conflicting checksums for the same version must stop migration and must not be silently normalized.
- Re-running migrations must not alter existing version/checksum history.
- Missing required schema objects, constraints, or runtime authority is a failure.
- Unknown or unexecuted checks remain **UNVERIFIED**; they must never be labeled PASS.
- Do not lock production readiness until the exact-SHA PostgreSQL gate and independent re-performance pass.

## Known evidence from historical run

A historical PostgreSQL Concurrency workflow run reported a duplicate `schema_version` publication for version 2 (`UniqueViolation`). That run is evidence of a past failure, not proof of the current source state. The conflict-safe publisher and current dedicated-database concurrency test require a fresh run on the exact current commit before this finding can be closed.

## Final evidence record

| Gate | Required evidence | Status |
|---|---|---|
| Fresh database migration | Exact-SHA PostgreSQL run | UNVERIFIED |
| Migration repeatability | Identical ordered version/checksum pairs | UNVERIFIED |
| Catalog/schema validation | Catalog query output and assertions | UNVERIFIED |
| Production entrypoint boot | Startup log + Canonical Ledger authority assertion | UNVERIFIED |
| Lifecycle/deep reconciliation | Integration-test output and matched report | UNVERIFIED |
| Restart/recovery | No duplicate movement; evidence remains consistent | UNVERIFIED |
| Independent re-performance | Reviewer/run record on same SHA | OPEN |

No PASS status is implied by this document.