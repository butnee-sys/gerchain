# EA-35 CI Failure Triage — Evidence Record

Status: IN PROGRESS / NOT LOCKED
Scope: canonical production runtime, PostgreSQL migration serialization, and value-truth evidence. This record does not include product-layer/SHUUD readiness.

## Evidence reviewed

### 1. core-gates — failed
- Workflow run: 36542458205 (run #2905)
- Job: 114820010500
- Observation: pytest collection stopped with 9 errors.
- Root cause shown by runner log: `services/gerchain_runtime.py:275` contained a literal escaped newline sequence inside a Python source line, producing `SyntaxError: unexpected character after line continuation character`.
- Interpretation: a source-generation/escaping defect, not a failing business invariant. The test suite did not reach execution.
- Current branch source inspection: the corresponding runtime region no longer contains that malformed function text. This is source inspection only; it is not proof that the current branch passes the same workflow.
- Required closure: rerun core-gates on the exact current branch head and preserve the run URL/SHA and complete test result.

### 2. PostgreSQL Concurrency — failed
- Workflow run: 36542458201 (run #1618)
- Job: 117550062477
- Observation: 5 passed, 1 failed.
- Failed test: `postgres/tests/test_concurrency.py::test_migrations_are_serialized_and_checksum_is_stable`.
- Root cause shown by runner log: concurrent migration publication raised `psycopg.errors.UniqueViolation` for `schema_version_pkey`, version 2.
- Interpretation: migration serialization/publication was not proven under concurrent execution at that tested revision.
- Current branch source inspection: migration runner now uses a session-level PostgreSQL advisory lock, reconciles duplicate legacy version rows, establishes a unique version index when absent, and publishes via `INSERT ... ON CONFLICT (version) DO NOTHING`, followed by checksum verification. This is a plausible corrective implementation, not a passing test result.
- Required closure: rerun the concurrency test against clean PostgreSQL and repeat it enough times to exercise competing migration runners; require exact checksum stability and no duplicate publication or lock leak.

### 3. SHUUD Command Layer — failed, tracked separately
- Workflow run: 36542458292 (run #1713)
- Job: 109320860172
- Root cause: test collection failed because the workflow installed a limited dependency set without `cryptography`, which is required at import time by DEE security.
- Scope decision: SHUUD/product readiness is outside this EA-35/EAI gate. Do not use this failure as evidence for or against the canonical value-flow gate. It remains a separate CI dependency issue.

### 4. SHUUD Sandbox Smoke — failed, tracked separately
- Workflow run: 36542458204 (run #1762)
- Job: 111562910351
- Root cause: API startup failed because `cryptography` was missing; the smoke lifecycle and restart/recovery assertions were skipped.
- Scope decision: separate product-layer gate, not proof of EAI production readiness.

## Positive evidence observed
- CodeQL Advanced run associated with the reviewed revision: success.
- CORE Operating Reconciliation run associated with the reviewed revision: success.
- A Snyk commit status was successful for the reviewed commit.
- These checks do not supersede the failed core-gates or PostgreSQL concurrency run.

## Production entrypoint / schema gate
Current branch source inspection shows the production entrypoint calls `ProductionRuntimeFactory`, runs PostgreSQL migrations, checks PostgreSQL connectivity, verifies required canonical tables/columns and key constraints, then requires canonical Ledger authority. This is static inspection only. It does not prove clean-database migration, boot, lifecycle execution, restart recovery, or independent re-performance.

## Exit criteria
Do not mark EA-35 or EAI production-ready until all of the following are attached to one exact commit SHA:
1. core-gates passes, with no collection errors.
2. PostgreSQL migration concurrency test passes on a clean database and repeated concurrent attempts.
3. Production entrypoint boots from a clean PostgreSQL instance using the canonical migration chain.
4. Lifecycle evidence covers CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, and READ.
5. Replay/idempotency/conflict, transaction rollback, concurrent access, process restart/recovery, and deep value-truth reconciliation pass.
6. Migration history/checksums and final schema inspection are preserved as artifacts.
7. Independent re-performance is recorded.
8. All unresolved items remain explicitly OPEN; no inferred GREEN status.
