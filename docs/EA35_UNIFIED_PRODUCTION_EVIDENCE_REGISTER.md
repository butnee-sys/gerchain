# EA-35 — Unified Production Evidence Register

Status: IN PROGRESS / NOT LOCKED
Current evidence target commit: 8fe3cb3949f0d3bc172a89119318a7081cf2f843
Evidence inspected: 2026-10-15
Repository: https://github.com/butnee-sys/gerchain
Branch: feat/ea35-production-lock-candidate

## 1. Exact-SHA run identity and completion

Each run below was fetched from the GitHub Actions API. The returned run metadata reports status `completed`, conclusion `success`, and exact `head_sha` `8fe3cb3949f0d3bc172a89119318a7081cf2f843`.

| Gate | Run ID | Job | Job result | Run URL |
|---|---:|---|---|---|
| PostgreSQL Production Runtime | 38554672120 | production-runtime (115820737718) | SUCCESS | https://github.com/butnee-sys/gerchain/actions/runs/38554672120 |
| EA-35 Production PostgreSQL Evidence | 38554672125 | production-postgresql-evidence (115820738405) | SUCCESS | https://github.com/butnee-sys/gerchain/actions/runs/38554672125 |
| EA-36 Independent PostgreSQL Transaction Graph | 38554672123 | ea36-postgresql (115820737788) | SUCCESS | https://github.com/butnee-sys/gerchain/actions/runs/38554672123 |
| core-gates | 38554672102 | core-gates (115820738025) | SUCCESS | https://github.com/butnee-sys/gerchain/actions/runs/38554672102 |
| CORE Operating Reconciliation | 38554672099 | core-reconciliation (115820737675) | SUCCESS | https://github.com/butnee-sys/gerchain/actions/runs/38554672099 |
| CodeQL Advanced | 38554672281 | run completed successfully | SUCCESS | https://github.com/butnee-sys/gerchain/actions/runs/38554672281 |
| SHUUD Command Layer | 38554672284 | run completed successfully | SUCCESS | https://github.com/butnee-sys/gerchain/actions/runs/38554672284 |
| SHUUD Sandbox Smoke | 38554672107 | run completed successfully | SUCCESS | https://github.com/butnee-sys/gerchain/actions/runs/38554672107 |
| Snyk commit status | n/a | security/snyk (butnee-sys) | SUCCESS | https://app.snyk.io/org/butnee-sys/pr-checks/c448c994-69b3-4d07-85ed-c21d4343f044 |

## 2. Job-step verification

The job-step API was inspected for production runtime, EA-35, EA-36, and core-gates. All reported steps were completed successfully, including:
- Verify canonical production runtime boot
- Upload PostgreSQL production runtime evidence
- Run deep value truth reconciliation on PostgreSQL
- Upload PostgreSQL evidence
- Run independent EA-36 PostgreSQL transaction graph
- Upload EA-36 evidence
- Run core structure and boundary tests

The production runtime job log includes PostgreSQL 16.15 startup and an intentionally invalid SQL statement used to exercise migration-failure rollback. This log entry is not by itself a test failure; the JUnit evidence below reports the migration rollback test passed.

## 3. Downloaded artifact and content hash verification

The following artifacts were downloaded from the completed exact-SHA runs, ZIP contents inspected, and SHA-256 hashes independently computed from the downloaded ZIP bytes and extracted JUnit XML bytes.

| Artifact | Artifact ID | ZIP size (bytes) | ZIP SHA-256 | Extracted JUnit XML | XML SHA-256 | JUnit result |
|---|---:|---:|---|---|---|---|
| postgres-production-runtime-junit | 11888062319 | 446 (GitHub metadata) | 085803f47f0adeb52d34e99a5101e2353726c392d7e5afc21282c7ffae91718a | postgres-production-runtime.xml | ed5eb9ad28293de1972d2e2d01c604615e3ac129bd6758810555da9f84546af5 | 2 tests, 0 failures, 0 errors |
| ea35-postgres-deep-reconciliation | 11887694560 | 700 (GitHub metadata) | a1deb60f151c29c525a50251f8bcf7d11c356a3357e4e6a4e366e174237a9799 | ea35-postgres-deep-reconciliation.xml | fc2e1c979b464ec5e1b5aa55fb3e4fe66030c2ddcd8d089554496864c42fe47e | 18 tests, 0 failures, 0 errors |
| ea36-postgresql-reperformance | 11889181276 | 417 (GitHub metadata) | 03c85fcf63aed0f7e2c7d6a5e9c6978fecd0f0a59ae8453343e01e0fb7f0dc4f | ea36-postgresql-reperformance.xml | 8900c0985842d98f0180c982324af43ad46ab93db658a224648b00faf2d5f1f7 | 1 test, 0 failures, 0 errors |

The JUnit reports' embedded timestamps are 2026-10-14 11:10:41Z (runtime), 2026-10-14 11:11:29Z (EA-35), and 2026-10-14 11:11:15Z (EA-36). All three artifacts were listed as present and not expired at inspection time.

## 4. Historical failed run — explicitly not the current head

Older commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` had failed runs:
- PostgreSQL Concurrency: https://github.com/butnee-sys/gerchain/actions/runs/36542458201
- core-gates: https://github.com/butnee-sys/gerchain/actions/runs/36542458205

The core-gates log identifies a Python SyntaxError in `services/gerchain_runtime.py` around the FUND method, caused by literal `\\n` text in source. These runs report `head_sha=e860f502f3e1a2d56fd873ad2faab7b1ab630740`; they are historical failures, not the current branch head. Current branch head `8fe3cb3949f0d3bc172a89119318a7081cf2f843` has its own completed successful runs recorded in section 1. The old failed runs remain in the evidence trail and must not be erased or relabeled as successful.

## 5. What this evidence proves — and does not prove

Supported by exact-SHA evidence:
- CI runs completed successfully on the current branch head.
- The canonical production runtime boot tests passed against a PostgreSQL 16.15 service container.
- Two production-runtime JUnit tests passed, including failed-migration rollback.
- EAI/EA-35 deep value-truth reconciliation ran on PostgreSQL: 18 tests passed.
- EA-36 independent transaction-graph re-performance ran on PostgreSQL: 1 test passed.
- Downloaded JUnit artifact contents were inspected and their ZIP/XML SHA-256 values recomputed.

Not established by these CI artifacts:
- Deployment and migration execution against the actual target production environment.
- Live environment identity, release image digest, applied schema version, and post-deployment health.
- IAM/MFA and privileged-access review.
- Main-branch protection/ruleset configuration and approval governance.
- Operational restart/recovery drill in the target environment.
- Signed independent human/third-party audit.

## 6. Gate decision

**NO PRODUCTION LOCK YET.** Exact-SHA CI and PostgreSQL test evidence is now materially stronger and artifact contents have been inspected, but production deployment provenance, governance controls, and target-environment recovery evidence remain open. Do not infer production-ready from successful CI alone.

Lock can be considered only after every required gate is evidenced closed or a scoped exception is formally approved, and the final evidence register remains pinned to an immutable commit SHA.
