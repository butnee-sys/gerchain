# EA-35 Workflow Evidence Register

Status: **IN PROGRESS / NOT LOCKED**  
Repository: `butnee-sys/gerchain`  
Evidence review date: 2026-10-11 (UTC+08:00)

## Scope and evidence rule

This register records the workflow results returned by GitHub for commit
`e860f502f3e1a2d56fd873ad2faab7b1ab630740` (production entrypoint factory-call correction).
These are historical run results associated with that commit; they are **not proof that
the current branch tip has passed**. Re-run both gates on the exact current candidate SHA
before using them as release evidence.

## Workflow records

| Gate | Commit association | Run ID | Job ID | Conclusion | Log | Artifacts |
|---|---|---:|---:|---|---|---|
| PostgreSQL Concurrency | `e860f502f3e1a2d56fd873ad2faab7b1ab630740` | 36542458201 | 113464773986 | **FAIL** | [Job log](https://github.com/butnee-sys/gerchain/actions/runs/36542458201/job/113464773986) | None returned by GitHub artifact listing |
| CORE Operating Reconciliation | `e860f502f3e1a2d56fd873ad2faab7b1ab630740` | 36542458262 | 109320859904 | **PASS** | [Job log](https://github.com/butnee-sys/gerchain/actions/runs/36542458262/job/109320859904) | None returned by GitHub artifact listing |

Run pages:
- [PostgreSQL Concurrency run](https://github.com/butnee-sys/gerchain/actions/runs/36542458201)
- [CORE Operating Reconciliation run](https://github.com/butnee-sys/gerchain/actions/runs/36542458262)

## Failure analysis — PostgreSQL Concurrency

The job log reports:

```text
FAILED postgres/tests/test_concurrency.py::test_migrations_are_serialized_and_checksum_is_stable
psycopg.errors.UniqueViolation:
duplicate key value violates unique constraint "schema_version_pkey"
DETAIL: Key (version)=(2) already exists.
1 failed, 5 passed
```

This run's failure proves the migration publication race existed in the source executed by that run.
The current branch's `postgres/migrations.py` now contains both a session-scoped PostgreSQL
advisory lock and `INSERT ... ON CONFLICT (version) DO NOTHING` followed by a checksum
read-back check. **That source-level mitigation is not execution proof.** The concurrency
workflow must be re-run on the exact current candidate SHA and pass before this gate can be
marked PASS.

## Successful gate

The CORE Operating Reconciliation job log reports `5 passed in 1.00s`.
This is a pass for that workflow's reconciliation integration suite only; it does not replace
the PostgreSQL migration-concurrency gate, nor does it prove production entrypoint boot,
full escrow lifecycle, restart recovery, or independent re-performance.

## Current evidence decision

- PostgreSQL Concurrency: **FAIL (historical run); current-source re-performance REQUIRED**
- CORE Operating Reconciliation: **PASS (historical run; exact current-SHA re-performance REQUIRED)**
- Artifacts: **none returned**; the job logs and run pages are the currently available evidence.
- Production entrypoint boot against PostgreSQL: **NOT VERIFIED**
- Full EAI production readiness: **NOT VERIFIED**
- Production lock: **NOT AUTHORIZED**

Release evidence must bind each passing run to the exact tested commit SHA, run ID, job ID,
job log URL, artifact identifier or explicit `none`, and conclusion. Never promote a
historical run to current-candidate evidence.
