# GerChain CORE — Audit Evidence Index

**Audit scope:** GerChain CORE
**Frozen baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`
**Current technical baseline:** `62594d16e926aa084c73f326eb77445d57fd4267`

## Evidence register

| Evidence ID | Area | Evidence location | Status |
|---|---|---|---|
| E-CORE-001 | Atomic release / idempotency | `persistence/atomic_release.py` + CORE tests | GREEN |
| E-CORE-002 | PostgreSQL concurrency | `.github/workflows/postgres-concurrency.yml` + PostgreSQL tests; PR #67 | GREEN |
| E-CORE-003 | Abandoned `PROCESSING` recovery | `persistence/atomic_release.py` + recovery tests; PR #63 | GREEN |
| E-CORE-004 | Operating reconciliation | `persistence/reconciliation.py` + `tests/test_operating_reconciliation.py`; PR #64 | GREEN |
| E-CORE-005 | CORE reconciliation CI | `.github/workflows/core-reconciliation.yml` | GREEN |
| E-CORE-006 | DEE key management | `tests/test_dee_key_management.py` | GREEN |
| E-CORE-007 | DEE security | `tests/test_dee_security.py` | GREEN |
| E-CORE-008 | CORE/SHUUD boundary | CORE-only PostgreSQL workflow + scope-boundary evidence; PR #67 | GREEN |
| E-CORE-009 | CodeQL | `.github/workflows/codeql.yml` + successful run evidence | GREEN |
| E-CORE-010 | PwC frozen baseline | Frozen SHA and prior PwC evidence set | FROZEN |
| E-GOV-001 | IAM / MFA | `GC-IDM-001/002` evidence package | MISSING |
| E-GOV-002 | Privileged access review | Organizational access inventory/review records | MISSING |
| E-GOV-003 | Main branch governance | Branch protection/ruleset evidence | UNVERIFIED |
| E-CI-001 | Post-merge main CI | Merge commit `62594d16...` workflow association | UNVERIFIED |

## Evidence retention rule

For final audit submission, retain the relevant workflow run IDs, job summaries, test output, commit SHA, pull-request merge record, and any organizational evidence outside GitHub in the designated audit evidence repository.

## Evidence quality rule

Evidence must be traceable, dated, scope-specific, and tied to the audited software version. Screenshots or narrative statements alone are not sufficient where machine-verifiable evidence is available.


## EA-35 exact-SHA production evidence — 2026-10-09

**Audited code SHA at evidence snapshot:** `e366596c9fedccb7c7f6d4df5eae32ab2a1a2940`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Decision:** **BLOCKED / NOT LOCKED**. Do not interpret queued or pending workflow runs as passing evidence.

| Required evidence runner | Exact-SHA run ID | Observed status | Conclusion | Artifact status |
|---|---:|---|---|---|
| Production PostgreSQL Re-performance | 37870328559 | queued | none | not yet available |
| FINAL Exact-SHA Full Suite | 37870328588 | queued | none | not yet available |
| EA-35 Value Truth PostgreSQL | 37870328635 | queued | none | not yet available |
| production-postgres | 37870328651 | queued | none | not yet available |
| DEE Security Gate | 37870328548 | queued | none | not yet available |
| independent-postgresql-evidence | 37870328649 | queued | none | not yet available |
| EAI PostgreSQL Production Proof | 37870328648 | queued | none | not yet available |
| production-postgresql-reperformance | 37870328831 | queued | none | not yet available |
| production-postgresql-gate | 37870328672 | queued | none | not yet available |
| core-gates | 37870328826 | queued | none | not yet available |
| CORE Operating Reconciliation | 37870328747 | queued | none | not yet available |
| CodeQL Advanced | 37870328785 | queued | none | not yet available |

The same SHA also had push-triggered PostgreSQL/production runs queued, including run IDs `37870323818`, `37870323814`, `37870323783`, `37870323839`, `37870323809`, `37870323816`, `37870323780`, `37870323807`, `37870323850`, `37870323804`, `37870323871`, `37870323805`, `37870323867`, `37870323808`, `37870323840`. Push runs `37870323860` and `37870323781` were cancelled. None of these observations is a successful completion.

The available combined commit status on the previous code SHA showed only `security/snyk` success; that is not sufficient to satisfy the required production/PostgreSQL and independent evidence gates. The core-gates artifact list was empty while its job was queued.

**Runner capacity/evidence blocker:** Many overlapping workflow definitions are triggering duplicate PostgreSQL, production, EAI, security, and full-suite runs concurrently. The runs above remain queued with null conclusions. The available GitHub connection does not provide a supported action to provision runner capacity or dispatch/restart a queued workflow. Required checks must be allowed to execute (or repository Actions/runner availability repaired) before the Evidence Index can record success.

**Exact-SHA lock:** NOT CREATED. EA-35 remains **IN PROGRESS / BLOCKED / NOT LOCKED** until every required runner completes successfully on the same exact SHA and its job details/artifacts are verified. The evidence-status note is `docs/EA35_EXACT_SHA_EVIDENCE_STATUS.md`; it is a blocker record, not a lock record.
