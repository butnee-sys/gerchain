# EA-35 — Consolidated Evidence Register and Canonical PostgreSQL Gate

Status: **IN PROGRESS / NOT LOCKED**
Scope: Fundamental architecture + EAI / Canonical PostgreSQL runtime. Product layers remain out of scope.
Branch: `feat/ea21-transaction-aware-ledger`

## Evidence interpretation

Historical successful runs remain recorded as historical evidence for the SHA they executed. They are not proof of a later SHA. Only the canonical PostgreSQL gate run against the exact candidate SHA can establish current production verification.

## Previously GREEN technical evidence retained

| Area | Prior evidence | Historical verdict | Boundary |
|---|---|---|---|
| Atomic release/idempotency | E-CORE-001; CORE tests and PostgreSQL evidence | GREEN | Candidate SHA re-performance required |
| PostgreSQL concurrency | E-CORE-002; `.github/workflows/postgres-concurrency.yml`; PR #67 | GREEN | Candidate SHA re-performance required |
| Abandoned PROCESSING recovery | E-CORE-003; recovery tests; PR #63 | GREEN | Candidate SHA re-performance required |
| Operating reconciliation | E-CORE-004; `persistence/reconciliation.py`; `tests/test_operating_reconciliation.py`; PR #64 | GREEN | Not equivalent to deep value-truth reconciliation |
| CORE reconciliation CI | E-CORE-005; `.github/workflows/core-reconciliation.yml` | GREEN | Candidate SHA re-performance required |
| DEE key management/security | E-CORE-006/007; key-management and security tests | GREEN | Does not prove organizational IAM/MFA |
| CodeQL | E-CORE-009; prior successful run evidence | GREEN | Candidate SHA run still required |
| PwC baseline | E-CORE-010; frozen SHA `274f45c83ce088e2229a2628e3a80403a68503df` | FROZEN | Historical baseline only |
| PostgreSQL production re-performance | Run `36317914217`, SHA `890a78f36dcfe161e195da649b3cd124133d6535` | SUCCESS | That SHA only |
| Production PostgreSQL Runtime | Run `36317914351`, SHA `890a78f36dcfe161e195da649b3cd124133d6535` | SUCCESS | That SHA only |
| production-postgres-smoke | Run `36317914313`, same SHA | SUCCESS | That SHA only |
| production-postgres-proof | Run `36317914446`, same SHA | SUCCESS | That SHA only |
| production-postgresql-gate | Run `36317914344`, same SHA | SUCCESS | That SHA only |
| PostgreSQL production verification | Run `36317914254`, same SHA | SUCCESS | That SHA only |
| EAI PostgreSQL Reperformance | Run `36317914266`, same SHA | SUCCESS | That SHA only |

These are not erased or downgraded. They remain historical, scope-specific GREEN evidence. They cannot be silently promoted to the current production-entrypoint/migration-guard code.

## Canonical next gate

Workflow: `.github/workflows/canonical-postgres-gate.yml`

It must run against one exact candidate SHA using PostgreSQL 16 and must capture:
1. Compile and regression-test logs.
2. Actual PostgreSQL connection/version.
3. Migration concurrency, checksum atomicity, duplicate-publication and legacy escrow upgrade tests.
4. Production lifecycle and entrypoint tests.
5. Real PostgreSQL production runtime boot.
6. Exactly migration versions 1–16 in `schema_version`, with each stored checksum equal to the checksum computed from the exact checked-out migration source and non-null `applied_at`.
7. PostgreSQL catalog evidence for canonical escrow-state constraint and validated canonical constraints.
8. Deep value-truth reconciliation test output.
9. An uploaded artifact named `canonical-postgres-evidence-<exact SHA>`, including `manifest.json`, `commit-sha.txt`, migration rows/checksums, and test logs.

## Exact-SHA result register

| Field | Verdict |
|---|---|
| Candidate SHA | Pending exact-SHA gate result |
| Workflow run ID / attempt | Pending |
| Workflow conclusion | NOT VERIFIED |
| PostgreSQL version/database | Pending gate output |
| Migration history 1–16 | Pending manifest/database output |
| Schema/constraint validation | Pending catalog output |
| Test report bundle | Pending artifact inspection |
| Artifact retained | Pending |
| Production lock | NOT CREATED |

A queued workflow, empty status list, prior SHA success, or source-code inspection is not a PASS.

## Non-CI closure gates

- Organizational IAM/MFA and privileged-access evidence: **MISSING**.
- Main-branch ruleset/protection evidence: **UNVERIFIED**.
- Independent re-performance by an independent reviewer: **OPEN**.
- Legacy value-authority isolation and final read-only/removal disposition: **OPEN**.
- Final architecture/EAI production lock: **NOT CREATED**.

## Decision

**IN PROGRESS / NOT LOCKED.** Retain the previous GREEN evidence with its SHA and scope; close the next gate only when the real PostgreSQL workflow, migration history, schema inspection, tests, and artifact are all tied to the same exact candidate SHA.