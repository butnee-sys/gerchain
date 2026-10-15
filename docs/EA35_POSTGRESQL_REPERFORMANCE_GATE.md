# EA-35 PostgreSQL Re-performance Gate

Status: **IN PROGRESS / NOT LOCKED**

This document records observed CI evidence and the gates required before production lock. It is not a production certification.

## Evidence observed

Repository: `butnee-sys/gerchain`

- CORE Operating Reconciliation: run [36542458262](https://github.com/butnee-sys/gerchain/actions/runs/36542458262) completed successfully.
- PostgreSQL Concurrency: run [36542458201](https://github.com/butnee-sys/gerchain/actions/runs/36542458201) failed.
- core-gates: run [36542458205](https://github.com/butnee-sys/gerchain/actions/runs/36542458205) failed.
- SHUUD Command Layer: run [36542458292](https://github.com/butnee-sys/gerchain/actions/runs/36542458292) failed.
- Snyk status for commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740`: success. This is a security check only and does not supersede failed tests.

## Failure evidence

### Runtime syntax error

The `core-gates` job log shows Python collection failed in `services/gerchain_runtime.py` because a `fund()` implementation was stored with literal escaped newline sequences. Nine test modules failed collection as a consequence. This proves that the affected workflow revision was not test-clean; it does not by itself prove the current branch still contains that defect.

### PostgreSQL migration concurrency

The PostgreSQL concurrency job log records a duplicate-key failure on `schema_version_pkey`, version `2`, during concurrent migration execution. The log also records repeated “there is already a transaction in progress” warnings. The invalid escrow state rejection was enforced by the database CHECK constraint and is not, by itself, a failure of the protection mechanism.

The current migration runner source describes a session-level advisory lock and transactional schema-version publication. This source inspection is not a substitute for a fresh passing PostgreSQL concurrency run on the exact current commit.

## Required closure evidence

1. Record the exact current branch head SHA.
2. Run Python syntax/collection checks and the targeted runtime/factory tests at that SHA.
3. Run PostgreSQL concurrency and migration tests against a clean PostgreSQL database; repeat migration to verify idempotency and concurrency serialization.
4. Run the production runtime factory/entrypoint boot against PostgreSQL and verify the canonical ledger authority flag.
5. Exercise commit, rollback, idempotent replay, conflicting replay, and recovery after interruption.
6. Run deep value-truth reconciliation and retain output covering Ledger movements, Escrow aggregate, Witness, Outbox, Idempotency, and integrity hashes.
7. Bind each workflow run and artifact to the exact tested commit SHA.
8. Require independent re-performance before production lock.

## Lock rule

Do not mark a gate GREEN based solely on source inspection, successful security scanning, or an unrelated passing workflow. Missing, stale, or non-matching-SHA evidence remains **UNVERIFIED**. Failed exact-SHA tests remain **BLOCKED** until corrected and rerun.

## Current disposition

**EA-35: IN PROGRESS / NOT LOCKED.**

No production-ready declaration is authorized by the evidence recorded here.
