# EA-35 Exact-SHA Evidence Gate — BLOCKED / NOT LOCKED

**Repository:** `butnee-sys/gerchain`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Exact current branch SHA checked:** `262c2c898f5be014abb57dc1ad0a390c6d5364fc`  
**Checked:** 2026-10-09 (GitHub Actions API snapshot)  
**Decision:** **BLOCKED — DO NOT DECLARE EA-35 LOCKED**

## Acceptance criteria

EA-35 may be locked only when each required runner for this exact SHA has `status=completed` and `conclusion=success`, the corresponding run/job IDs and artifact inventory are recorded, required evidence artifacts are present and reviewed, the Evidence Index references this exact SHA, and the exact-SHA lock record is committed after all checks finish.

## Exact-SHA workflow evidence observed

| Workflow | Run ID | Event | Exact head SHA | Observed status | Conclusion | Artifact evidence |
|---|---:|---|---|---|---|---|
| core-gates | 37840325304 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | pending (job queued) | none | none listed |
| CodeQL Advanced | 37840325590 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| Production PostgreSQL Re-performance | 37840325186 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| production-postgres | 37840325353 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| independent-postgresql-evidence | 37840325331 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| FINAL Exact-SHA Full Suite | 37840325661 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| EAI PostgreSQL Production Proof | 37840325352 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| production-postgresql-reperformance | 37840325422 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| production-postgresql-gate | 37840325570 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| DEE Security Gate | 37840325454 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| EA-35 Value Truth PostgreSQL | 37840325528 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |
| CORE Operating Reconciliation | 37840325513 | pull_request | 262c2c898f5be014abb57dc1ad0a390c6d5364fc | queued | none | not yet available |

Additional push-triggered runs for this SHA include run IDs 37840320991, 37840320977, 37840321008, 37840321070, 37840321114, 37840321123, 37840321101, 37840321151, 37840321118, and more. At least two push runs (37840321160 and 37840321120) were cancelled. These do **not** constitute successful evidence.

## Status-check observation

The combined commit status endpoint returned one success status: `security/snyk (butnee-sys)`. That is only one check; it does not satisfy the full production/PostgreSQL/reconciliation/independent-runner acceptance gate. The same SHA's Actions jobs remain queued/pending with null conclusions. The `core-gates` run's artifact inventory was empty at the time checked.

## Workflow topology issue

The branch contains numerous overlapping PostgreSQL/production/EAI/EA-35 workflow files. The exact-SHA run listing shows many duplicate runs queued concurrently. This is a runner-execution/evidence blocker, not a passing test result. Consolidate the authoritative required checks before treating the runner queue as a complete release gate; retain one canonical PostgreSQL/core gate and explicitly enumerated independent/security checks.

## Required next actions

1. Obtain GitHub Actions execution capacity and let/restart the exact-SHA required workflows until each required job completes.
2. Confirm every required run has `head_sha=262c2c898f5be014abb57dc1ad0a390c6d5364fc`, `status=completed`, `conclusion=success`.
3. Fetch each run's jobs and step results; inspect logs for the PostgreSQL boot, schema initialization/migration, canonical value-flow tests, deep reconciliation, recovery, and exact-SHA full suite.
4. Fetch each required run's artifacts; verify artifact names, digests/expiry, and contents where required. An empty artifact list is not evidence of success.
5. Update the Evidence Index with final run IDs, job IDs, artifact references, and exact SHA only after all acceptance checks pass.
6. Commit a separate exact-SHA lock record whose target SHA is this tested commit, and verify no code changes were made after testing. Any code change invalidates this evidence lock and requires rerun.

## Lock decision

**EA-35: IN PROGRESS / BLOCKED / NOT LOCKED.**  
**Exact-SHA evidence lock: NOT CREATED**, because required runs are not completed-success and the required artifact inventory is absent. Creating a success/lock record now would misrepresent the available machine evidence.
