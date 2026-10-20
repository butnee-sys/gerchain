# Production Lock Gate Decisions — Fundamental Architecture + EAI

**Decision date:** 2026-10-20  
**Repository:** `butnee-sys/gerchain`  
**Branch reviewed:** `feat/ea21-transaction-aware-ledger`  
**Reviewed branch tip:** `0d27cad6b3d935eae985925c5b0ba3cd7a9858d9`  
**Decision:** **PRODUCTION LOCK NOT AUTHORIZED — OPEN GATES REMAIN**  
**Scope:** Fundamental architecture and EAI (Escrow as Infrastructure).  
**Excluded:** SHUUD, SHIID, SANDBOX, and product/application gates.

## 1. Decision semantics

The canonical architecture freeze and EAI scope/authority rules remain frozen. That is not equivalent to certifying the whole implementation production-ready. A production lock requires every mandatory technical and governance gate below to be CLOSED on a controlled evidence basis. A historical successful run on a different SHA is valid evidence for that execution SHA only; it does not establish that every gate passed together on the reviewed branch tip.

The repository contains a separate scope-management record titled “FINAL LOCK”. Its own text explicitly says it is not a new test run or external certification. Therefore that scope-management decision must not be interpreted as a production-readiness certification.

## 2. Gate-by-gate decision

| ID | Gate | Decision | Evidence / closure condition |
|---|---|---|---|
| G-01 | Canonical architecture and adapter boundaries | **FROZEN / CLOSED as design** | `docs/DEE_ARCHITECTURE_FREEZE.md`, frozen 2026-09-14. Any change requires an explicit approved architecture-change proposal. |
| G-02 | EAI definition and scope | **CLOSED as design** | EAI means Escrow as Infrastructure; it is not a new layer, not G3 itself, and not a second Escrow Engine. |
| G-03 | Single value authority | **IMPLEMENTED; production lock pending** | Canonical Ledger tables and transaction-aware boundary are defined. Legacy stores still require physical freeze/removal or a formally approved, enforceable read-only/archive disposition. |
| G-04 | Production PostgreSQL boot and value-flow | **VERIFIED for historical execution SHA only** | `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md` records successful PostgreSQL gate evidence on `f11fcb6411f1458c7bb4696566a695a52141b0c3`. It does not prove all mandatory gates on the current reviewed tip. |
| G-05 | Versioned migration chain on clean PostgreSQL | **HISTORICALLY VERIFIED; current-tip re-performance unverified** | Preserve migration history/checksums and attach the successful run to the exact reviewed SHA. |
| G-06 | Upgrade from supported existing production schema | **OPEN** | Must run against the explicitly supported prior schema; verify migration history, schema guard, constraints, indexes, and preserved data. Fresh-database boot is not a substitute. |
| G-07 | FUND / LOCK / RELEASE / REFUND / CANCEL / SETTLEMENT | **HISTORICALLY VERIFIED; same-SHA closure open** | Historical PostgreSQL value-flow evidence exists. Require all operations and persisted postconditions on the same reviewed SHA as the migration and recovery gates. |
| G-08 | Deep value-truth reconciliation | **HISTORICALLY VERIFIED; same-SHA closure open** | Reconcile movement, escrow, witness, outbox, idempotency, and integrity hash; report must contain zero unexplained issues. |
| G-09 | Crash / restart / abandoned-operation recovery | **OPEN** | Existing evidence does not establish a full process interruption + PostgreSQL restart + recovery + replay run on the same SHA as all other production gates. Prove no duplicate value movement. |
| G-10 | Idempotency under replay and conflict | **IMPLEMENTED / PARTIALLY VERIFIED** | Unit/integration evidence exists; same-SHA end-to-end replay after restart remains part of G-09. Same key with different fingerprint must fail closed. |
| G-11 | Legacy value stores and bypasses | **OPEN** | Legacy endpoints are fail-closed, but physical store removal/archive or enforceable read-only state is not independently closed. Prove no production write path uses MoneyLedger, ReleaseAccount, AccountBalance, SQLite or application-owned balance truth. |
| G-12 | CI required workflows on exact branch tip | **UNVERIFIED** | Current branch tip reviewed: `0d27cad6b3d935eae985925c5b0ba3cd7a9858d9`. The available combined-status query returned no statuses, and the commit-associated workflow endpoint returned no runs. Historical successes on other SHAs cannot satisfy this gate. |
| G-13 | Security scan / Snyk | **VERIFIED only for historical SHA** | Snyk success was recorded for `f11fcb6411f1458c7bb4696566a695a52141b0c3`; retain the report and run a current-tip scan or explicitly establish an approved immutable-release relationship. |
| G-14 | IAM / MFA / privileged-access governance | **OPEN / MISSING organizational evidence** | Attach organizational evidence for privileged identity, MFA, access review, and emergency access. Source code/tests alone cannot close this gate. |
| G-15 | Main-branch governance / branch protection | **OPEN / UNVERIFIED** | Verify repository rulesets/protection, required reviews/checks, bypass permissions, and release authority. |
| G-16 | Independent re-performance / oracle package | **OPEN** | Independent reviewer must tie migration, production flow, crash recovery, reconciliation, and CI artifacts to the same immutable source revision. |
| G-17 | Final evidence bundle and immutable production lock | **OPEN** | Must include exact SHA, workflow/run IDs, job conclusions, migration logs, reconciliation output, recovery/replay output, security report, governance evidence, and independent sign-off. |

## 3. Non-negotiable production invariants

1. One canonical Ledger balance/movement authority.
2. One canonical durable Escrow state machine.
3. One authoritative Witness path and one production Outbox path.
4. Value release follows Decision → Authorization → Release.
5. Unknown, missing, inconsistent, or unverified required conditions fail closed.
6. A committed value movement must have matching escrow, movement, witness, outbox, idempotency, and integrity evidence as defined by the canonical contract.
7. Recovery must not duplicate value movement or create a second truth authority.
8. No downstream or legacy actor may directly mutate the protected authority, policy, or execution state.
9. Scope freeze does not override failed, missing, stale, or SHA-mismatched evidence.

## 4. Final decision

- **Canonical architecture design:** FROZEN.
- **EAI design and authority boundary:** FROZEN.
- **Historical PostgreSQL/EAI technical gates:** VERIFIED for their recorded execution SHAs only.
- **Whole fundamental architecture + EAI production readiness:** **NOT CERTIFIED / NOT LOCKED**.
- **Production deployment approval:** **DENIED until G-06, G-09, G-11, G-12, G-14, G-15, G-16 and G-17 are closed**, and all required technical gates are tied to the same release SHA.
- **SHUUD/SHIID/SANDBOX:** excluded; their results neither block nor satisfy these gates.

This is a gate decision record, not a claim that tests were run by this commit. Do not mark any open gate green without its required evidence.
