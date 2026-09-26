# EA-35 PostgreSQL Production Evidence

Status: **PASS — EA-35.13 PostgreSQL production gate**

Execution commit:
- `3ebb049ce4bc5a30172dbdb70882417f2ead7d0f`

Repository branch:
- `feat/ea21-transaction-aware-ledger`

## Verified GitHub Actions evidence

All runs below are associated with the exact execution commit above.

1. PostgreSQL production re-performance
   - Run: `36204225958`
   - Job: `postgres-reperformance`
   - Conclusion: **success**
   - Verified production runtime construction and PostgreSQL deep value-truth tests.

2. PostgreSQL production verification
   - Run: `36204225841`
   - Job: `postgres-production`
   - Conclusion: **success**
   - Verified production PostgreSQL bootstrap, full value flow, and deep value reconciliation.

3. Production PostgreSQL runtime
   - Run: `36204225910`
   - Job: `production-postgresql-runtime`
   - Conclusion: **success**
   - Verified production entrypoint boot against PostgreSQL and production PostgreSQL value-flow proof.

## Schema integrity correction

The production migration directory contained two files using migration version `002`, which violated the migration executor's uniqueness contract and would block production boot.

Resolved:
- retained `002_canonical_production.sql`
- removed duplicate `002_canonical_production_schema.sql`
- made `condition_desc` nullable-compatible with the canonical ORM contract

The migration set is now version-unique:
`001, 002, 003, 004, 005, 006, 007, 008`.

## Closure statement

EA-35.13 PostgreSQL production boot and value-flow verification is **evidenced PASS** on the exact execution commit.

This does **not** by itself declare the overall EAI / fundamental architecture production lock. Remaining gates include independent re-performance, evidence reconciliation, legacy authority retirement/freeze verification, security/IAM assurance, observability, recovery/DR, and final release governance.
