# EA-35 Current-SHA PostgreSQL verification trigger

This marker exists solely to trigger the branch PostgreSQL production smoke workflows against the current canonical production runtime and migration runner.

Required interpretation: this file is not evidence by itself. Evidence is the GitHub Actions result for the commit that adds this marker.


Current-SHA re-verification trigger: execute the canonical PostgreSQL production gates against this commit; prior successful SHAs are not sufficient for final lock.

Re-triggered: 2026-10-09 exact-branch verification after production-entrypoint constructor correction.

## 2026-10-10 failure analysis

The 2026-10-08 workflow attempt associated with the earlier production-entrypoint commit is historical failure evidence, not current-branch verification.

Observed failures from job logs:
- PostgreSQL concurrency: duplicate `schema_version(version=2)` publication in the historical run.
- Core gate: Python collection failed on a historical `services/gerchain_runtime.py` syntax error caused by literal escaped newline characters in a method body.
- SHUUD command/sandbox: missing `cryptography` dependency in the historical workflow image. This is tracked separately from the fundamental-architecture/EAI production gate and must not be used as evidence of EAI production readiness.

Current-branch source inspection confirms the migration publisher now uses `INSERT ... ON CONFLICT (version) DO NOTHING`, verifies the stored checksum, and the runtime source contains normal Python method bodies. Source inspection alone is not runtime evidence.

Required current-SHA re-performance:
1. Compile the production entrypoint, runtime factory, runtime, migration runner, and deep reconciliation module.
2. Run the isolated PostgreSQL migration-concurrency test against a fresh database.
3. Run the canonical PostgreSQL boot/schema guard.
4. Run PostgreSQL deep value-truth reconciliation tests.
5. Capture exact-SHA workflow jobs and logs. Any failure remains OPEN and must be corrected before production lock.

Status: IN PROGRESS / NOT LOCKED. This document records failure analysis only; it does not assert a passing test or production lock.
