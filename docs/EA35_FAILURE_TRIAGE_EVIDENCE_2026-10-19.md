# EA-35.56 — Failure Triage Evidence (2026-10-19)

Status: **TRIAGED / FIX-AND-REPERFORM REQUIRED / NOT LOCKED**

This record captures observed GitHub Actions failures. It does not claim that these historical runs represent the current branch tip or that a fix has passed.

## Evidence A — `core-gates` collection failure

- Workflow run: https://github.com/butnee-sys/gerchain/actions/runs/36542458205
- Run ID: `36542458205`; job ID: `114820010500`
- Observed result: failure during pytest collection, before the test suite could establish a pass.
- Log evidence: `tests/test_production_runtime_factory.py` and `tests/test_production_runtime_factory_postgres.py` import `services/gerchain_runtime.py`; Python reports `SyntaxError: unexpected character after line continuation character` at line 275. The source line contained literal escaped newline sequences (`\n`) inside the `fund` method definition/body.
- Interpretation: source-generation/commit corruption prevented module import. This is a hard collection blocker, not a behavioral test failure.
- Required closure: confirm the current branch version has real line breaks; run `python -m compileall` and exact-SHA `core-gates`; preserve successful run evidence.

## Evidence B — PostgreSQL migration concurrency/publication failure

- Workflow run: https://github.com/butnee-sys/gerchain/actions/runs/36542458201
- Run ID: `36542458201`; job ID: `117550062477`
- Observed result: `postgres/tests/test_concurrency.py::test_migrations_are_serialized_and_checksum_is_stable` failed; 5 passed, 1 failed.
- Exact database error: `psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "schema_version_pkey"`, detail `Key (version)=(2) already exists.`
- PostgreSQL server log corroborates a duplicate `INSERT INTO schema_version(version, checksum) VALUES ($1, $2)` while two migration sessions were racing.
- Interpretation: concurrent migration runners both reached schema-version publication without the race being safely serialized/idempotently resolved for this execution. The expected invariant—one authoritative checksum row per migration version—was not demonstrated.
- Required closure: reproduce on a fresh disposable PostgreSQL database with two independent sessions; verify advisory-lock acquisition and transaction boundaries; make publication conflict-safe without accepting a conflicting checksum; assert one row per version and exact checksum equality; rerun the exact-SHA PostgreSQL gate.

## Additional observed PostgreSQL log

The same PostgreSQL job log shows a deliberate invalid state update rejected by `escrows_state_check`. That rejection is expected negative-test behavior and is not the reported failure. The failing test is the duplicate `schema_version` publication.

## Release decision

- Historical CI is evidence of blockers, not evidence of current branch status.
- A green security status alone does not close `core-gates` or PostgreSQL concurrency.
- Do not mark production ready until the current exact SHA passes source compilation, `core-gates`, fresh PostgreSQL migration concurrency, lifecycle/rollback/recovery/deep reconciliation, and production-entrypoint/schema validation.
- Every required result must be linked to the same commit SHA. Independent re-performance remains a separate gate.

**Current gate:** EA-35 — IN PROGRESS / NOT LOCKED.