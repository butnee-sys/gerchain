# Production PostgreSQL Migration Gate — Evidence Record

Status: **PENDING EXECUTION — NOT LOCKED**

This record is deliberately not a production-ready attestation. It identifies the exact PostgreSQL proof required for the canonical migration chain and binds the resulting report to a single Git commit and GitHub Actions run.

## Required proof

1. Apply the exact canonical migration registry, versions 001–017, to a clean PostgreSQL database.
2. Upgrade a legacy database containing the old `escrows.state` CHECK constraint and preserve all rows while replacing/drift-repairing the constraint.
3. Verify every `schema_version` row and SHA-256 runner checksum against the exact checked-out migration source; require exactly versions 1–17, no gaps or duplicates, and non-null application timestamps.
4. Run `assert_canonical_production_schema()` against the live PostgreSQL catalog. Require exactly one validated `escrows_state_canonical_check` whose accepted states are CREATED, FUNDED, LOCKED, RELEASED, REFUNDED, and CANCELLED; reject legacy/duplicate state constraints and any missing or weakened canonical constraints.
5. Bind the evidence manifest, PostgreSQL test logs, migration checksums, workflow run ID/attempt, and checked-out HEAD to the same commit SHA.

## Acceptance rule

The gate is accepted only if the PostgreSQL workflow exits successfully on the exact evidence SHA and uploads its evidence bundle. A Snyk-only success, static test result, migration-file count, or a workflow result from another SHA is not sufficient.

## Result fields

- Tested commit SHA: pending
- PostgreSQL workflow run ID / attempt: pending
- Clean database migration 001–017: pending
- Legacy escrow constraint upgrade: pending
- Schema version + checksum match: pending
- Live catalog assertion: pending
- Evidence artifact + SHA256SUMS: pending
- Final decision: **NOT LOCKED**

The master work plan must not be reported as 100% until all acceptance conditions above and all other plan gates are independently evidenced.
