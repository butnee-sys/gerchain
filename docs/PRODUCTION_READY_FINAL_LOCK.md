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
