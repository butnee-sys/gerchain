# EA-35 CI Re-performance Evidence

Status: IN PROGRESS / NOT LOCKED

## Evidence captured

- Commit under inspection: `e860f502f3e1a2d56fd873ad2faab7b1ab630740`
- PostgreSQL Concurrency workflow run: [36542458201](https://github.com/butnee-sys/gerchain/actions/runs/36542458201)
- Job: `postgres-concurrency` (job ID `113464773986`)
- Result: **FAILURE** — 5 passed, 1 failed.
- Failing test: `postgres/tests/test_concurrency.py::test_migrations_are_serialized_and_checksum_is_stable`
- Observed PostgreSQL error: `UniqueViolation: duplicate key value violates unique constraint "schema_version_pkey"; Key (version)=(2) already exists.`

This is a real failure, not a green result. It means the migration concurrency proof did not pass for the inspected commit.

## Current-code observation

The current branch version of `postgres/migrations/__init__.py` uses a transaction-scoped advisory lock and publishes version rows with `INSERT ... ON CONFLICT (version) DO NOTHING`, followed by a checksum verification. This appears intended to address duplicate publication, but **the current branch's exact commit has not yet been shown by a successful fresh PostgreSQL run**. The failed run above predates proof of that correction and must not be treated as proof that the current version passes.

## Required re-performance

1. Run the PostgreSQL concurrency test against the exact current branch commit using a truly fresh isolated database.
2. Verify two distinct backend PIDs, one row for each migration version 1–13, stable checksums after rerun, and no duplicate version publication.
3. Run the canonical production schema initialization against PostgreSQL and verify all required tables and columns.
4. Exercise atomic value movement, rollback, idempotent replay/conflict, witness/outbox integrity, and restart/recovery on PostgreSQL.
5. Attach the exact commit SHA and successful workflow run to this evidence file before changing any gate to GREEN.

## Decision

No production lock. The PostgreSQL migration concurrency gate remains **RED / UNVERIFIED** until fresh evidence passes on the exact current commit. A successful Snyk status does not substitute for PostgreSQL integration evidence.


## Fresh exact-head run — 2026-10-11

Evidence commit (head SHA): `1318184f2b32d5f2ecad0720386cab665652e53d`

### Passing targeted PostgreSQL gates

- [EAI PostgreSQL Re-performance run 38112250559](https://github.com/butnee-sys/gerchain/actions/runs/38112250559): **SUCCESS**. The job used PostgreSQL 16.15; production factory asserted canonical ledger authority; required tables were present with no missing columns; targeted test segment reported **19 passed**; deep value-truth reconciliation tests completed; commit-bound artifact was uploaded.
- [PostgreSQL migration gate run 38112250610](https://github.com/butnee-sys/gerchain/actions/runs/38112250610): **SUCCESS**.
- [FINAL EAI/CORE Exact-SHA Gate run 38112250562](https://github.com/butnee-sys/gerchain/actions/runs/38112250562): both `production-eai` and `core-and-migration` jobs **SUCCESS**, including canonical and independent PostgreSQL migration-concurrency re-performance and production-factory contract checks.

### Failing broader regression gates

- [Production PostgreSQL Gate run 38112250578](https://github.com/butnee-sys/gerchain/actions/runs/38112250578): **FAILURE**. Full regression segment reported **115 failed, 846 passed, 2 skipped**. A large cluster of legacy verifier/witness tests fails because settlement now requires a DEE Root of Trust and Trinity proof; failures include `ValueError: DEE Root of Trust and Trinity proof are required for atomic settlement`. The subsequent PostgreSQL lifecycle steps were skipped due to fail-fast behavior.
- [Production Gate run 38112250584](https://github.com/butnee-sys/gerchain/actions/runs/38112250584): **FAILURE**. Full suite reported **174 failed, 971 passed, 41 skipped**. Failures include the same settlement trust-contract mismatch and unrelated SHUUD measurement/restart/config test failures.

### Interpretation

The earlier duplicate `schema_version` publication failure was observed on an earlier commit/run. The fresh targeted PostgreSQL migration and factory gates now pass on the evidence commit above. However, the full production regression is not green. Do not mark the complete production system green from targeted passes alone.

Next work:
1. Keep the strict settlement trust contract; update affected tests/fixtures to provide valid Root of Trust and Trinity evidence rather than weakening production checks.
2. Triage unrelated SHUUD tests separately; they are outside the current EAI production-lock scope, but must not be misreported as passing.
3. Re-run the full production regression and PostgreSQL value lifecycle on the exact new commit.
4. Only then reassess the production lock.

Decision remains **IN PROGRESS / NOT LOCKED**.
