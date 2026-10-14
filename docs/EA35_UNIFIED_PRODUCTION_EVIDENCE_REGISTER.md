# EA-35 — Unified Production Evidence Register

Status: IN PROGRESS / NOT LOCKED
Evidence target commit: 31db2abcf1a91a5b9e9436c8495bfd67e0aa0ac2
Evidence captured: 2026-10-14
Repository: https://github.com/butnee-sys/gerchain

## 1. Exact-SHA CI and security evidence

All workflow runs below report head SHA `31db2abcf1a91a5b9e9436c8495bfd67e0aa0ac2` in GitHub's artifact metadata where artifacts are available.

| Gate | Run ID | Result | Evidence |
|---|---:|---|---|
| EA-35 Production PostgreSQL Evidence | 38551475961 | SUCCESS | Artifact `ea35-postgres-deep-reconciliation`, ID 11886627484 |
| EA-36 Independent PostgreSQL Transaction Graph | 38551475997 | SUCCESS | Artifact `ea36-postgresql-reperformance`, ID 11886169950 |
| PostgreSQL Production Runtime | 38551476074 | SUCCESS | Artifact `postgres-production-runtime-junit`, ID 11886204803 |
| core-gates | 38551475976 | SUCCESS | Fundamental architecture, PostgreSQL concurrency, production runtime boot steps completed |
| CodeQL Advanced | 38551475990 | SUCCESS | Analyze (python) job completed successfully |
| Snyk | n/a | SUCCESS status | Commit status context `security/snyk (butnee-sys)`; target URL below |
| CORE Operating Reconciliation | 38551475810 | SUCCESS | Workflow run completed successfully |

Run URL pattern: https://github.com/butnee-sys/gerchain/actions/runs/<RUN_ID>

Snyk status target: https://app.snyk.io/org/butnee-sys/pr-checks/19e58d28-d763-4de6-8713-de2a2bde93ae

## 2. Artifact integrity metadata

These are GitHub Actions artifact-service SHA-256 digests, not independently recomputed hashes of the unzipped files.

| Artifact | Artifact ID | Size (bytes) | Service SHA-256 digest | Expires |
|---|---:|---:|---|---|
| ea35-postgres-deep-reconciliation | 11886627484 | 705 | 51ae1a1cfc1d9a31ab0fb4ec23d6bb18b5e7768a3c8d2f1313603f7f7b9a8bee | 2027-01-12 |
| ea36-postgresql-reperformance | 11886169950 | 418 | 8bddc621a48268e6e7ee2c0a280aec7b8defe141439cf629c7c116767a1c268b | 2027-01-12 |
| postgres-production-runtime-junit | 11886204803 | 448 | ecdb0f3b754933ae9a60ec080666a4850e16f06509d14634cca1266c43004813 | 2027-01-12 |

Artifacts were reported as present and not expired when this register was assembled. Artifact ZIP contents, internal JUnit XML hashes, reconciliation report contents, and internal-file SHA-256 values have NOT yet been independently recomputed or cross-compared. Do not treat service digests as proof of report-content equivalence.

## 3. Migration concurrency gate

The exact-SHA `core-gates` workflow completed successfully. Its job step `PostgreSQL concurrency gate` is recorded as completed with conclusion SUCCESS under run 38551475976. The independent production PostgreSQL runtime and reconciliation workflows also completed successfully on this SHA.

This records CI outcomes; it does not by itself prove a production deployment migration was applied to a live customer database. Migration provenance, schema version, and deployment-environment identity must be attached separately before production lock.

## 4. Independent transaction-graph re-performance

Workflow run 38551475997 completed successfully; job `ea36-postgresql` ran `Run independent EA-36 PostgreSQL transaction graph` and uploaded artifact 11886169950. Artifact metadata binds the run to the target SHA. The artifact contents still need to be downloaded, inspected, and hashed independently.

## 5. Gate inventory

| Gate | Status | Evidence / next action |
|---|---|---|
| PostgreSQL production runtime boot | CI SUCCESS | Inspect JUnit contents and verify schema migration identity |
| Deep value-truth reconciliation | CI SUCCESS | Inspect report contents; independently recompute report-file SHA-256 |
| Independent transaction-graph re-performance | CI SUCCESS | Inspect artifact; confirm scope and assertions |
| core-gates / PostgreSQL concurrency | CI SUCCESS | Preserve exact-SHA run/job record |
| CodeQL | CI SUCCESS | Exact-SHA workflow run 38551475990 |
| Snyk | SUCCESS status | Commit status context and target URL recorded |
| Artifact service digests | RECORDED | Re-download ZIPs and verify ZIP/content hashes independently |
| IAM/MFA | OPEN / NOT VERIFIED HERE | Attach policy/configuration evidence and privileged identity inventory |
| Privileged-access review | OPEN / NOT VERIFIED HERE | Attach dated reviewer, scope, findings, remediation |
| Main-branch governance | OPEN / NOT VERIFIED HERE | Verify branch protection/rulesets, required checks, review rules |
| Production deployment | OPEN / NOT VERIFIED HERE | Attach environment deployment ID, image digest, schema version, health check |
| Recovery / restart / duplicate-movement prevention | OPEN / NOT VERIFIED HERE | Attach PostgreSQL-backed failure/restart/replay evidence |
| Migration applied to target production environment | OPEN / NOT VERIFIED HERE | Record target environment identity, migration version, and post-migration checks |
| Independent human/third-party audit | OPEN / NOT VERIFIED HERE | Attach signed review or explicitly approved exception |

## 6. Lock decision

**NO PRODUCTION LOCK.** CI run success is positive evidence, but governance, deployment, recovery, migration provenance, and artifact-content integrity remain open. The lock decision must not be inferred from green workflow badges alone.

Production lock may be considered only after every required gate is either evidenced closed or has a formally approved, scoped exception, and the final register points to immutable exact-SHA artifacts.
