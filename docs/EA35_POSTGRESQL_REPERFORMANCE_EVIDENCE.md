# EA-35 PostgreSQL Re-performance Evidence

Status: IMPLEMENTED / EVIDENCE RECORDED / NOT LOCKED

Branch: `feat/ea21-transaction-aware-ledger`
Evidence SHA: `7a99dd82554a3f348c2c5ad34420a14fb3628e40`

## Verified PostgreSQL runs

The following GitHub Actions runs executed against PostgreSQL 16 service containers and completed successfully at the evidence SHA:

| Run | Workflow | Result | Scope |
|---|---|---|---|
| 35894575593 | PostgreSQL production re-performance | SUCCESS | Production runtime boot + FUND + LOCK + RELEASE + deep value-truth reconciliation |
| 35894575779 | PostgreSQL production proof | SUCCESS | Canonical PostgreSQL production flow proof |
| 35894575911 | production-postgresql-proof | SUCCESS | PostgreSQL canonical proof |
| 35894575630 | PostgreSQL production smoke | SUCCESS | Canonical Ledger account creation + transaction-aware movement + replay idempotency |
| 35894580238 | Production PostgreSQL Runtime | SUCCESS | Real PostgreSQL production entrypoint boot + PostgreSQL runtime verification |
| 35894580310 | PostgreSQL production verification | SUCCESS | PostgreSQL production verification |
| 35894580318 | Production PostgreSQL verification | SUCCESS | PostgreSQL production verification |
| 35894580352 | EAI Production PostgreSQL Re-performance | SUCCESS | PostgreSQL factory construction + deep value-truth test suite |

## Important evidence

The strongest end-to-end run is `35894575593`.

Its executed test:
`tests/integration/test_production_postgresql_reperformance.py`

It verified, against a real PostgreSQL service:

- Canonical production runtime construction.
- Canonical Ledger authority.
- Durable account/escrow initialization.
- FUND: source -> escrow.
- LOCK: FUNDED -> LOCKED.
- RELEASE: escrow -> beneficiary.
- Canonical Ledger balances after release.
- Durable escrow terminal state RELEASED.
- Three witness records.
- Deep value-truth reconciliation matched.

The smoke run `35894575630` additionally verified:

- transaction-aware Ledger mutation;
- persisted movement evidence;
- operation and escrow binding;
- replay of the same transaction;
- exactly one persisted movement after replay.

The production-runtime run `35894580238` verified the actual `production_entrypoint.py` boot path against PostgreSQL and completed successfully.

## Migration integrity

Migration discovery was independently checked on the branch.

The migration directory now contains exactly one migration for each version 001 through 008:

- 001_concurrency.sql
- 002_canonical_persistence.sql
- 003_ea25_durable_idempotency.sql
- 004_ea26_value_flow_persistence.sql
- 005_ea35_canonical_production.sql
- 006_canonical_escrow_lifecycle_hardening.sql
- 007_canonical_production_compat.sql
- 008_ea35_idempotency_compat.sql

A duplicate version-002 migration was removed because the migration loader correctly rejects duplicate migration versions.

## Remaining release gates

This evidence does NOT by itself declare the architecture production-locked.

Remaining gates include:

1. Consolidate/resolve redundant PostgreSQL workflows with inconsistent historical assertions.
2. Independent re-performance by a separate execution/reviewer.
3. Security/IAM/MFA production evidence.
4. Full recovery/DR evidence.
5. Final cross-store reconciliation evidence over the complete production dataset.
6. Final CI/release governance evidence.
7. Formal production lock decision after all gates are closed.

GREEN in this document means the specific GitHub Actions execution completed successfully; it is not an external certification or overall production approval.
