# EA-35.53 — Exact-SHA CI Failure Forensics

Status: **IN PROGRESS / NOT LOCKED**  
Purpose: preserve the observed failure signatures and require fresh exact-SHA re-performance. This document does not claim that either gate is now green.

## Evidence inspected

### 1. Historical `core-gates` collection failure

GitHub Actions run: `36542458205`  
Job: `114820010500`  
Step: `Run core structure and boundary tests`

The job stopped during pytest collection with **9 collection errors**. The repeated traceback root was:

```
tests/test_runtime_postgres_release.py:3
  from services.gerchain_runtime import GerchainRuntime
services/gerchain_runtime.py, line 275
  SyntaxError: unexpected character after line continuation character
```

The failing source line in that run contained literal escaped newline text (`\\n`) followed by a pasted multi-line implementation, rather than valid Python line breaks. All nine collection errors therefore share one import-time syntax failure; they are not nine independently established defects.

Current branch source must be recompiled and the same `core-gates` workflow rerun on its new exact commit before this is considered resolved.

### 2. Historical PostgreSQL migration concurrency failure

GitHub Actions run: `36542458201`  
Job: `117550062477`  
Step: `Run PostgreSQL concurrency suite`

Observed failure:

```
psycopg.errors.UniqueViolation:
duplicate key value violates unique constraint "schema_version_pkey"
DETAIL: Key (version)=(2) already exists.
```

The job summary reported `1 failed, 5 passed`, with the failure at:
`postgres/tests/test_concurrency.py::test_migrations_are_serialized_and_checksum_is_stable`.

This is direct evidence that two migration runners historically attempted to publish version 2 concurrently. It is not acceptable to infer success from comments or source inspection alone. The latest exact-SHA PostgreSQL 16 run must demonstrate:
- both independent connections complete;
- one canonical row per version 1–16;
- no duplicate versions;
- all stored checksums match the canonical migration files;
- repeat application is idempotent;
- migration concurrency and checksum-mismatch cases fail closed as designed.

## Required re-performance

1. Compile `services/gerchain_runtime.py`, `production_entrypoint.py`, `services/gerchain_runtime_factory.py`, and `postgres/migrations.py`.
2. Rerun `core-gates` and retain the full collection/test logs.
3. Rerun the PostgreSQL 16 migration/concurrency gate against a fresh disposable database.
4. Record the exact commit SHA, workflow run IDs, job outcomes, `schema_version` rows 1–16, and expected-vs-stored checksum comparison.
5. Run production entrypoint boot and deep Canonical Ledger–Escrow–Witness–Outbox–Idempotency reconciliation on the same commit.
6. Keep production lock blocked until all required evidence is fresh and independently reproducible.

## Gate rule

Historical failure logs are forensic evidence, not current pass evidence. A source correction, successful compile, or successful unit test alone does not close either production gate.
