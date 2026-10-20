# PRODUCTION READY — FINAL LOCK REGISTER

**Document status:** CONTROLLED FINAL-LOCK REGISTER — PARTIAL LOCK ONLY  
**Repository:** `butnee-sys/gerchain`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Scope:** Fundamental architecture and EAI / Escrow as Infrastructure; CORE is one infrastructure component, not the whole scope. Product layers remain excluded until EAI is fully production-ready and separately locked.  
**Rule:** A previously verified GREEN/SUCCESS result is retained as locked evidence for that exact control and evidence scope. It is not automatically proof that the current branch, current schema, deployment, or entire platform is production-ready.

## 1. Lock decision

This register locks the previously documented GREEN/FROZEN controls listed in Section 2 as **evidence-scoped locks**. It does **not** falsely declare the entire platform PRODUCTION READY FINAL LOCK: current-branch exact-SHA CI, real PostgreSQL boot and lifecycle re-performance, complete migration evidence, independent re-performance, and organizational governance evidence must be retained before the global release lock can be issued.

**Global production status: IN PROGRESS / NOT LOCKED.**  
**Evidence-scoped controls: LOCKED at their stated scope, subject to the evidence freshness and baseline limitations below.**

No downstream actor may directly alter the authoritative truth, authority, policy, or core execution state of PDEIZ.

## 2. Previously accepted GREEN / SUCCESS evidence carried into this register

| Lock ID | Control / capability | Previously recorded evidence | Lock disposition | Boundary / limitation |
|---|---|---|---|---|
| PL-CORE-001 | Atomic release and idempotency | `persistence/atomic_release.py` and CORE tests | LOCKED — evidence scope | Historical CORE implementation evidence; does not prove current Canonical Ledger end-to-end cutover |
| PL-CORE-002 | PostgreSQL concurrency | `.github/workflows/postgres-concurrency.yml`, PostgreSQL tests, PR #67 evidence | LOCKED — evidence scope | Must not be treated as current-branch production PostgreSQL re-performance |
| PL-CORE-003 | Abandoned PROCESSING recovery | `persistence/atomic_release.py`, recovery tests, PR #63 evidence | LOCKED — evidence scope | Recovery evidence applies to the tested path and baseline |
| PL-CORE-004 | Operating reconciliation | `persistence/reconciliation.py`, `tests/test_operating_reconciliation.py`, PR #64 evidence | LOCKED — evidence scope | Does not replace deep movement/witness/outbox/idempotency reconciliation |
| PL-CORE-005 | CORE reconciliation CI | `.github/workflows/core-reconciliation.yml` | LOCKED — evidence scope | Current exact-SHA run must be verified before global lock |
| PL-CORE-006 | DEE key management | `tests/test_dee_key_management.py` | LOCKED — evidence scope | Repository test evidence, not external certification |
| PL-CORE-007 | DEE security | `tests/test_dee_security.py` | LOCKED — evidence scope | Repository test evidence, not external certification |
| PL-CORE-008 | CORE / SHUUD scope boundary | CORE-only PostgreSQL workflow and PR #67 evidence | LOCKED — evidence scope | Product-layer assurance remains out of scope for this lock |
| PL-CORE-009 | CodeQL security workflow | `.github/workflows/codeql.yml`, previously recorded successful run | LOCKED — historical evidence | Fresh exact-SHA CodeQL result still required for release |
| PL-CORE-010 | PwC evidence baseline | Frozen baseline `274f45c83ce088e2229a2628e3a80403a68503df` | FROZEN | Frozen baseline is not re-attestation of later changes |
| PL-EAI-001 | Canonical architecture freeze | `docs/DEE_ARCHITECTURE_FREEZE.md`, frozen blob `0940d8aae8858d34604eb9d7174a8afc636bb2f` | LOCKED | Changes require an explicit approved architecture-change proposal |
| PL-EAI-002 | Single production value-authority target | `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md` | DESIGN LOCKED | Physical legacy-store freeze/removal and live production verification remain open |
| PL-EAI-003 | Runtime operation cutover design | `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md` | IMPLEMENTED / EVIDENCE-SCOPED | FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ code paths exist; current exact-SHA and PostgreSQL run evidence remains required |
| PL-EAI-004 | Deep value-truth reconciliation contract implementation | `persistence/deep_value_reconciliation.py` and associated tests in branch history | IMPLEMENTED / EVIDENCE-SCOPED | No global pass claim without fresh test output and live PostgreSQL re-performance |
| PL-EAI-005 | Fail-closed legacy mutation endpoints | `api/v1.py` and `gerchain/web_ui.py` changes recorded in branch history | IMPLEMENTED / EVIDENCE-SCOPED | Must re-check exact current code and endpoint tests before global release |
| PL-EAI-006 | Canonical production runtime constructor and schema gate | `services/gerchain_runtime_factory.py`, `production_entrypoint.py` | IMPLEMENTED / NOT YET RELEASE-VERIFIED | Schema gate code exists; successful real PostgreSQL boot has not been established by this register |

## 3. Canonical invariants now protected by this register

1. One authoritative production Ledger: `gerchain_ledger_accounts` and `gerchain_ledger_movements`.
2. No production balance mutation outside `PostgreSQLAtomicLedger.transfer_in_transaction` or its approved canonical transaction boundary.
3. One durable Canonical Escrow state machine.
4. Decision → Authorization → Release is mandatory; no direct release.
5. No second authoritative Ledger, Witness Chain, or Escrow Engine.
6. One transaction must bind value movement, escrow transition, witness, outbox, and durable idempotency evidence.
7. Same idempotency key + same fingerprint replays; same key + different fingerprint conflicts.
8. Unknown/unresolved required conditions fail closed; they do not pass.
9. Balance equality alone is insufficient: value truth requires movement, escrow, witness, outbox, idempotency, and integrity reconciliation.
10. Self-recovery follows DETECT → ISOLATE → HOLD → DIAGNOSE → RECONCILE → RECOVER → VERIFY → AUDIT. Failed verification remains HOLD.
11. Legacy/in-memory/SQLite paths must not silently become production value authority.
12. Architecture changes require explicit approval and must preserve the frozen canonical boundaries.

## 4. Open gates — mandatory before GLOBAL PRODUCTION READY FINAL LOCK

| Gate | Required evidence | Status |
|---|---|---|
| G-01 Exact commit identity | Record the exact current branch commit SHA and associate all test/workflow results with it | OPEN |
| G-02 Fresh CI | Successful required workflow runs on that exact SHA; absent run data is UNVERIFIED, not GREEN | OPEN |
| G-03 Real PostgreSQL schema migration | Clean PostgreSQL instance, apply canonical migration registry, verify migration history and constraints | OPEN |
| G-04 Production entrypoint boot | Start `production_entrypoint.py` against PostgreSQL and retain boot/readiness/log evidence | OPEN |
| G-05 Lifecycle re-performance | CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, READ against PostgreSQL, including replay/conflict and rollback cases | OPEN |
| G-06 Deep value-truth reconciliation | Clean graph passes; intentionally corrupted graphs fail; no unexplained orphan/mismatch | OPEN |
| G-07 Recovery/restart | Restart/abandoned processing/recovery proves no duplicate value movement | OPEN |
| G-08 Legacy authority retirement | Prove legacy tables/paths are read-only, disabled, removed, or formally quarantined | OPEN |
| G-09 Independent re-performance | A reviewer can reproduce the evidence from a clean environment and exact SHA | OPEN |
| G-10 IAM/MFA and privileged access | Organizational identity, MFA, access review, and branch-governance evidence | MISSING / OPEN |
| G-11 Final evidence package | Test outputs, workflow run IDs, migration history, reconciliation report, deployment config, reviewer sign-off | OPEN |

## 5. Release rule

Global lock may be issued only when every mandatory gate in Section 4 is GREEN with retained, current evidence, or a documented risk acceptance is explicitly approved by the authorized owner. A historical GREEN status cannot be copied forward to a changed commit without re-performance.

At global lock:
- record exact commit SHA;
- attach exact-SHA CI run IDs and results;
- retain PostgreSQL migration and schema verification output;
- retain lifecycle and recovery test outputs;
- retain deep reconciliation report;
- record independent reviewer and sign-off;
- freeze this register and its evidence index.

## 6. Current disposition

**This commit adds the controlled final-lock register; it does not claim a platform-wide production release.**

- Previously documented GREEN/FROZEN controls are included as evidence-scoped locks.
- Canonical architecture remains frozen.
- EAI implementation remains in progress until live PostgreSQL and independent evidence close the remaining gates.
- Product layers remain outside this lock.
- Overall: **IN PROGRESS / NOT LOCKED**.


## 7. Required PostgreSQL proof gates — current execution record

The following three gates are mandatory, separate evidence items. A code review or a historical PostgreSQL run does not close them for the current lock candidate.

| ID | Required proof | Required retained artifact | Current status |
|---|---|---|---|
| PG-CONC-01 | Run two independent PostgreSQL connections/processes against the same empty migration registry concurrently. Prove advisory-lock serialization, no duplicate `schema_version.version`, no checksum disagreement, and stable results on a subsequent rerun. | Exact-SHA test output; both process results; before/after `schema_version` rows; duplicate/checksum assertions. | OPEN — NOT RE-PERFORMED ON CURRENT CANDIDATE |
| PG-SCHEMA-02 | Apply all 17 canonical migrations to a clean PostgreSQL database. Read the resulting schema and registry from PostgreSQL itself; verify versions 1–17, checksums, actual columns/indexes, CHECK/UNIQUE constraints, and `convalidated` for applicable constraints. | Exact-SHA migration log; 17 registry rows/checksums; catalog query output for tables, constraints and validation; rerun idempotency output. | OPEN — LIVE CATALOG EVIDENCE REQUIRED |
| PG-TRUTH-03 | Run `deep_reconcile_value_truth()` against a clean PostgreSQL dataset and prove every value movement binds to the correct Escrow, Witness, Outbox, Idempotency evidence and recomputed integrity hash. Include deliberate mismatch cases. | Exact-SHA clean report; negative-case report; movement-to-evidence linkage export; PostgreSQL connection/runtime details. | OPEN — POSTGRESQL VALUE-TRUTH REPORT REQUIRED |

### Execution rule

These gates must run against one recorded candidate SHA. Two independent PostgreSQL connections are required for PG-CONC-01; SQLite tests cannot substitute. PG-SCHEMA-02 must query PostgreSQL catalogs, not infer the schema from migration files. PG-TRUTH-03 must execute the actual reconciliation function against PostgreSQL rows, not a mocked or SQLite session.

No result has been marked PASS in this register until the corresponding live evidence is retained. The current GitHub source inspection establishes implementation intent only; it does not itself prove these three runtime properties.

## 8. Master-plan completion accounting

For progress reporting, the full MASTER WORK PLAN v1.0 is the 100% denominator. To avoid inflating progress, work is separated into (a) implementation/evidence already retained at a narrower scope and (b) global production-lock gates requiring current proof.

- **Implementation and scoped technical controls:** substantially implemented; retain only the controls and evidence explicitly listed in Sections 2–3.
- **Global FINAL LOCK:** **0% closed as a final release decision** until all mandatory gates are evidenced and approved. This does not mean 0% engineering work; it means no platform-wide lock has been issued.
- **Overall completion percentage:** **not yet defensibly computable from the current repository evidence alone**. The plan does not define weights for its heterogeneous workstreams, and assigning equal weights or a guessed percentage would misrepresent production readiness. A scored 100-point rubric must be agreed and applied to the actual gate evidence before publishing a numeric total.

Current decision remains **IN PROGRESS / NOT LOCKED**.


## 9. EA-35 PostgreSQL Re-performance — migration gate update (2026-10-19)

Workflow source: `.github/workflows/ea35-postgres-reperformance.yml`
https://github.com/butnee-sys/gerchain/blob/feat/ea21-transaction-aware-ledger/.github/workflows/ea35-postgres-reperformance.yml

Source inspection confirms the workflow definition is configured to:
- run a PostgreSQL 16 service;
- assert that the checked-out HEAD equals the expected evidence SHA;
- apply the canonical migration chain and assert `schema_version` versions exactly 1–17;
- rerun migrations and compare registry rows (including checksums and `applied_at`) and PostgreSQL constraints;
- exercise an upgrade path from the 001–014 prefix through later migrations;
- compare the live PostgreSQL registry to the 17-file canonical migration manifest; and
- capture a PostgreSQL schema snapshot and manifest carrying the same expected commit SHA.

**Evidence limitation:** during this update, the workflow definition and migration runner were inspected, but a successful run for the current candidate SHA and its retained artifacts were not retrieved. Therefore these checks are not counted as passed. A workflow file containing assertions is not equivalent to a passing run.

| ID | Acceptance criterion | Status |
|---|---|---|
| PG-MIG-01 | Live PostgreSQL `schema_version` contains exactly versions 1–17, with no duplicate version and non-empty checksums | OPEN — exact-SHA run artifact not verified |
| PG-MIG-02 | Second migration run changes no checksum, applied timestamp, or PostgreSQL constraint | OPEN — exact-SHA before/after evidence not verified |
| PG-MIG-03 | Live PostgreSQL schema snapshot and 17-migration manifest use the same exact commit SHA | OPEN — exact-SHA artifacts not verified |

### Gate decision

**PRODUCTION MIGRATION GATE — OPEN / NOT LOCKED**

EA-35 migration evidence completion: **0/3 gates verified = 0%**.

Overall PRODUCTION READY FINAL LOCK percentage remains **not yet defensibly computable**: the full plan has no approved weighted scoring rubric, and the available inspection does not prove current-run execution. This gate-specific 0% must not be presented as the percentage of engineering work completed.

### Next action

Retrieve or trigger the `EA-35 PostgreSQL Re-performance` workflow on the exact candidate SHA. Retain the run ID, job conclusions, and `artifacts/ea35` evidence package. Inspect PG-MIG-01, PG-MIG-02, and PG-MIG-03 against the actual artifacts. If any assertion fails, correct the migration/workflow and repeat on a new SHA. Do not issue the global production lock until these and all other mandatory gates are evidenced.
