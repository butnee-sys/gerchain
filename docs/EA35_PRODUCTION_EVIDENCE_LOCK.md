# EA-35 PostgreSQL Production Evidence Lock

## Evidence commit

- Exact evidence commit: `6a7802cf8530e2b890344e4a15c19e95007467f2`
- Branch: `feat/ea21-transaction-aware-ledger`
- Scope: Canonical PostgreSQL production persistence, EAI escrow-as-infrastructure production proof, value-flow integrity and deep reconciliation.

## Production gate

GitHub Actions run: `37555415350` — **SUCCESS**

Verified successfully on the exact evidence commit:

1. Exact evidence commit recorded.
2. Python syntax gate.
3. Production factory and canonical persistence.
4. Production entrypoint boot against PostgreSQL.
5. Concurrent PostgreSQL migration bootstrap.
6. Deep value-truth reconciliation suite.
7. EAI production re-performance.
8. Real PostgreSQL production value-flow gate.

## Independent evidence

- `independent-postgresql-evidence` run `37555415339` — **SUCCESS**
- Independent persisted-value verification completed successfully.
- `production-postgres` run `37555415368` — **SUCCESS**
- Production migration/boot, value flow, and deep value-truth suite completed successfully.
- `EAI PostgreSQL Production Proof` run `37555415365` — **SUCCESS**
- EAI PostgreSQL production proof completed successfully.

## Failure remediation

The preceding exact evidence commit exposed a migration-bootstrap race:

- PostgreSQL concurrency run `36542458201` failed at
  `test_migrations_are_serialized_and_checksum_is_stable`.
- Failure: duplicate `schema_version(version=2)`.

The remediation changed migration bootstrap to use one transaction-level PostgreSQL advisory lock for the entire migration transaction.

The remediation was then re-performed on the exact evidence commit above and passed the concurrent migration bootstrap gate.

## Production conclusion

The following are now **evidenced on the exact commit**:

- PostgreSQL is the production persistence boundary.
- Canonical Ledger authority is established at runtime.
- Production entrypoint boots against PostgreSQL.
- Migration bootstrap is concurrency-safe under the production test.
- Canonical value-flow operations pass the real PostgreSQL production gate.
- EAI production re-performance passes.
- Deep value-truth reconciliation passes.

This document does **not** declare the entire GerChain architecture globally production-locked. IAM/privileged-access governance, independent external attestation, release governance, disaster recovery and other master-plan gates remain separate controls.

Status: **EA-35 PostgreSQL PRODUCTION EVIDENCE = GREEN / EVIDENCE LOCKED**

Overall production readiness: **IN PROGRESS / NOT LOCKED**
