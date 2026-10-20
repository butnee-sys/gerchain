# EA-35 — Consolidated Evidence Register and Canonical PostgreSQL Gate

Status: **IN PROGRESS / NOT LOCKED**
Scope: Fundamental architecture + EAI / Canonical PostgreSQL runtime. Product layers remain out of scope.
Branch: `feat/ea21-transaction-aware-ledger`

<<<<<<< HEAD
## 1. Evidence rules

Evidence status is SHA-scoped. A successful historical run is retained as valid evidence for the code SHA it actually executed, but is not silently promoted as proof for later changes. The production lock requires a single exact-SHA evidence bundle from `.github/workflows/canonical-postgres-gate.yml`, plus all mandatory governance and independent-review evidence.

- **GREEN (historical, scope-specific)**: successful retained test/workflow evidence on the named historical SHA.
- **CURRENT SHA VERIFIED**: only after the canonical PostgreSQL workflow completes successfully on the exact candidate SHA and its artifact is inspected.
- **NOT VERIFIED**: queued, missing, incomplete, or unrelated status checks.
- **LOCKED**: prohibited until every mandatory gate and exception is formally resolved.

## 2. Previously verified technical evidence — retained, not discarded

| Evidence area | Historical evidence | Recorded result | Limit |
|---|---|---|---|
| Atomic release / idempotency | CORE test + PostgreSQL evidence; audit register E-CORE-001 | GREEN (historical) | Must be re-performed against candidate SHA |
| PostgreSQL concurrency | `.github/workflows/postgres-concurrency.yml`, PostgreSQL tests, PR #67; E-CORE-002 | GREEN (historical) | Candidate SHA gate still required |
| Abandoned PROCESSING recovery | Recovery tests, PR #63; E-CORE-003 | GREEN (historical) | Candidate SHA gate still required |
| Operating reconciliation | `persistence/reconciliation.py`, `tests/test_operating_reconciliation.py`, PR #64; E-CORE-004 | GREEN (historical) | Does not replace deep value-truth reconciliation |
| CORE reconciliation CI | `.github/workflows/core-reconciliation.yml`; E-CORE-005 | GREEN (historical) | Candidate SHA gate still required |
| DEE key management/security | `tests/test_dee_key_management.py`, `tests/test_dee_security.py`; E-CORE-006/007 | GREEN (historical) | Does not establish organizational IAM/MFA |
| CodeQL | Prior successful CodeQL run; E-CORE-009 | GREEN (historical) | Exact candidate SHA result must be checked |
| Frozen baseline | PwC baseline SHA `274f45c83ce088e2229a2628e3a80403a68503df`; E-CORE-010 | FROZEN | Not rewritten or extended by implication |
| PostgreSQL production re-performance | Run `36317914217`, historical execution SHA `890a78f36dcfe161e195da649b3cd124133d6535` | SUCCESS (historical) | Evidence for that SHA only |
| Production PostgreSQL Runtime | Run `36317914351`, same historical execution SHA | SUCCESS (historical) | Evidence for that SHA only |
| production-postgres-smoke | Run `36317914313`, same historical execution SHA | SUCCESS (historical) | Evidence for that SHA only |
| production-postgres-proof | Run `36317914446`, same historical execution SHA | SUCCESS (historical) | Evidence for that SHA only |
| production-postgresql-gate | Run `36317914344`, same historical execution SHA | SUCCESS (historical) | Evidence for that SHA only |
| PostgreSQL production verification | Run `36317914254`, same historical execution SHA | SUCCESS (historical) | Evidence for that SHA only |
| EAI PostgreSQL Reperformance | Run `36317914266`, same historical execution SHA | SUCCESS (historical) | Evidence for that SHA only |

These historical results are included as prior evidence, not thrown away. They do **not** prove that the newer production-entrypoint, migration-guard, or evidence-manifest changes pass on the current SHA.

## 3. Canonical gate contract

Workflow: `.github/workflows/canonical-postgres-gate.yml`

The gate uses PostgreSQL 16 and is expected to:
1. Compile production/persistence modules.
2. Collect and run CORE foundation regression tests.
3. Connect to the actual PostgreSQL service.
4. Re-perform migration checksum atomicity and migration-runner concurrency.
5. Re-perform legacy escrow constraint upgrade and data preservation.
6. Execute the canonical escrow lifecycle and production entrypoint contract.
7. Boot the production runtime against PostgreSQL and inspect required canonical tables.
8. Verify canonical migration versions **1–16**, database checksums against exact checked-out migration sources, and `applied_at` history.
9. Inspect PostgreSQL catalog constraints, including unique canonical escrow-state constraint and `convalidated = true`.
10. Run PostgreSQL deep value-truth reconciliation.
11. Upload `canonical-postgres-evidence-${{ github.sha }}` containing the migration manifest, exact commit SHA, logs, and available schema history.

## 4. Exact-SHA result record

| Field | Required evidence |
|---|---|
| Candidate commit SHA | The exact SHA checked out by the workflow |
| Workflow run / attempt | Run ID and attempt number |
| Workflow conclusion | `success` only |
| PostgreSQL version/database | Captured from the real service |
| Migration chain | Exactly versions 1–16, no gaps or duplicates |
| Migration history | Each version, checksum, and non-null `applied_at` |
| Source checksum match | Database checksum equals runner checksum for each migration at the candidate SHA |
| Schema | Required tables and columns present |
| Constraints | Canonical names, semantic definitions, uniqueness, and validation state verified |
| Test reports | Collection, CORE regression, migration, lifecycle, entrypoint, and deep-reconciliation logs |
| Artifact | Uploaded evidence bundle retained and inspectable |

No value is recorded as PASS merely because a workflow exists or is queued. The exact-SHA row must be filled only after run metadata, jobs, and artifact contents are inspected.

## 5. Remaining non-CI closure controls

These are not replaced by successful code tests:
- IAM / MFA and privileged-access organizational evidence: **MISSING**.
- Main-branch protection / ruleset evidence: **UNVERIFIED**.
- Independent re-performance by a reviewer independent of implementation: **OPEN**.
- Legacy value-authority isolation and final read-only/removal disposition: **OPEN** until demonstrated by code-path inventory and tests.
- Formal final lock: **NOT CREATED**.

## 6. Decision

The prior GREEN technical results remain registered with their historical scope and SHA. The candidate release remains **IN PROGRESS / NOT LOCKED** until the canonical PostgreSQL gate has a successful exact-SHA run and the uploaded evidence bundle proves migration history, schema state, and test results for that same SHA.
=======
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
| PostgreSQL production re-performance | Run `36317914217`, SHA `890a78f36dcfe161e195da649b3cd124133d6535` | 🟢 GREEN (historical; job success re-checked) | That SHA only; current candidate must re-run |
| Production PostgreSQL Runtime | Run `36317914351`, SHA `890a78f36dcfe161e195da649b3cd124133d6535` | SUCCESS | That SHA only |
| production-postgres-smoke | Run `36317914313`, same SHA | 🟢 GREEN (historical; job success re-checked) | That SHA only; current candidate must re-run |
| production-postgres-proof | Run `36317914446`, same SHA | 🟢 GREEN (historical; job success re-checked) | That SHA only; current candidate must re-run |
| production-postgresql-gate | Run `36317914344`, same SHA | 🟢 GREEN (historical; job success re-checked) | That SHA only; current candidate must re-run |
| PostgreSQL production verification | Run `36317914254`, same SHA | 🟢 GREEN (historical; job success re-checked) | That SHA only; current candidate must re-run |
| EAI PostgreSQL Reperformance | Run `36317914266`, same SHA | 🟢 GREEN (historical; job success re-checked) | That SHA only; current candidate must re-run |

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
| Migration history 1–17 | Pending manifest/database output |
| Schema/constraint validation | Pending catalog output |
| Test report bundle | Pending artifact inspection |
| Artifact retained | Pending |
| Production lock | NOT CREATED |

A queued workflow, empty status list, prior SHA success, or source-code inspection is not a PASS.

## Restored prior GREEN findings (scope-specific)

The seven PostgreSQL/EAI workflow runs above were queried again and their sole jobs were confirmed `completed` with `conclusion=success`. This restores their historical GREEN status in the register. The canonical gate workflow currently defines migration versions 1–17 (not 1–16); the exact-SHA artifact must prove the full 1–17 chain. The workflow runs above do not by themselves prove a later candidate SHA, and no downloadable artifacts were returned for these historical runs.

## Non-CI closure gates

- Organizational IAM/MFA and privileged-access evidence: **MISSING**.
- Main-branch ruleset/protection evidence: **UNVERIFIED**.
- Independent re-performance by an independent reviewer: **OPEN**.
- Legacy value-authority isolation and final read-only/removal disposition: **OPEN**.
- Final architecture/EAI production lock: **NOT CREATED**.

## Decision

**IN PROGRESS / NOT LOCKED.** Retain the previous GREEN evidence with its SHA and scope; close the next gate only when the real PostgreSQL workflow, migration history, schema inspection, tests, and artifact are all tied to the same exact candidate SHA.
>>>>>>> 17cedc21229b38b4e2972100d5698bbba22a660c
