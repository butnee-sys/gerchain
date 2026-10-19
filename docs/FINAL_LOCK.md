# FINAL LOCK — Master Production Work Plan

**Status:** PARTIAL GATE RECORD — NOT A PRODUCTION LOCK  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Production entrypoint correction commit:** `e860f502f3e1a2d56fd873ad2faab7b1ab630740`  
**Recorded:** 2026-10-19

## Scope and safety rule

The production target is the fundamental architecture and EAI (Escrow as Infrastructure), not CORE in isolation. Product-layer work remains outside this gate. No unverified architectural mutation may be applied automatically. The self-repair process may detect, isolate, hold, diagnose, reconcile, recover, verify, and audit; it must not rewrite architecture or authoritative truth without an approved change.

## Step 1 — Fundamental architecture inventory / map

**Disposition: CLOSED — INVENTORY / MAPPING DELIVERABLE COMPLETE.**  
The inventory and authority map are recorded in [`MASTER_PRODUCTION_WORK_PLAN_STEP1_INVENTORY_MAP.md`](MASTER_PRODUCTION_WORK_PLAN_STEP1_INVENTORY_MAP.md).

Step 1 records the frozen canonical layer path, authoritative owner for each foundational domain, production entrypoint/factory/migration registry, Canonical Ledger and durable Escrow boundaries, Witness/Outbox/Idempotency evidence paths, lifecycle operations, cross-store reconciliation graph, legacy/duplicate authorities, and residual release gates.

**Closure boundary:** this closes the source-repository inventory/mapping task only. It does not certify runtime behavior, PostgreSQL migrations, production boot, full lifecycle, recovery, current-tip CI, organizational IAM/MFA, or independent re-performance. These remain explicit production release gates. Step 1 closure must not be interpreted as permission to skip Step 2 or to mark the overall architecture/EAI production-ready.

## Step 2 — Error / duplicate / excess review

**Disposition: CLOSED — REVIEW AND CLASSIFICATION COMPLETE. Remediation and overall production lock remain separate, open gates.**

The repository review and final dispositions are recorded in [`MASTER_PRODUCTION_WORK_PLAN_STEP2_ERROR_DUPLICATE_EXCESS.md`](MASTER_PRODUCTION_WORK_PLAN_STEP2_ERROR_DUPLICATE_EXCESS.md). The review identified and dispositioned these classes of risks:
- Multiple legacy balance authorities (MoneyLedger, ReleaseAccount, AccountBalance) versus Canonical Ledger.
- Legacy application/API mutation paths that could bypass controlled runtime boundaries.
- Legacy/in-memory entrypoint risk versus the production PostgreSQL runtime.
- Factory/entrypoint contract mismatch: entrypoint called `ProductionRuntimeFactory.create(...)` as though it were a static factory and expected Canonical Ledger authority, while the factory implementation constructed the legacy PostgreSQL release path.
- Schema initialization is not a substitute for versioned, reviewed production migrations.
- Deep value-truth reconciliation must bind canonical movement to escrow, witness, operation-matched outbox, idempotency and integrity hash.

The latest correction changes the entrypoint to instantiate `ProductionRuntimeFactory(ProductionRuntimeConfig(...), engine=engine)`, then call `factory.create()`. The factory now initializes canonical persistence metadata and configures Canonical Ledger authority. This is source-level evidence only until runtime and PostgreSQL checks pass.

### Step 2 final disposition

- Duplicate value authorities are classified; Canonical Ledger is the sole intended production value authority.
- Legacy/API/UI mutation bypasses are classified with fail-closed disposition; current-tip execution evidence remains a separate verification requirement.
- Production entrypoint/factory mismatch is corrected at source level.
- Migration, reconciliation, operation-matched outbox, idempotency and integrity evidence requirements are explicitly assigned.
- Legacy physical store removal/archive is tracked as remediation, not hidden inside the review status.

**Step 2: CLOSED.** This is closure of the review step, not certification that all listed remediations have been executed or that production is ready.

## Exact-commit CI evidence

Commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` returned one reported commit status:
- `security/snyk (butnee-sys): success`

This is **not** a complete CI result. No pytest/workflow-suite pass or PostgreSQL runtime evidence is established by that status. All unreported checks remain UNVERIFIED.

## Required remaining gates

1. Run the repository's full CI/test workflow on the exact commit.
2. Run canonical persistence integration tests against a real PostgreSQL service.
3. Apply reviewed/versioned migrations; do not rely on `metadata.create_all` as the production migration plan.
4. Boot the production entrypoint using PostgreSQL and verify Canonical Ledger authority.
5. Execute lifecycle and failure/replay cases, then run deep value-truth reconciliation.
6. Re-perform independently and attach immutable logs/artifacts to the exact commit.

## Lock decision

**Step 2 — Error / Duplicate / Excess review: CLOSED.** Findings, canonical ownership, fail-closed dispositions and residual gates are recorded in [`MASTER_PRODUCTION_WORK_PLAN_STEP2_ERROR_DUPLICATE_EXCESS.md`](MASTER_PRODUCTION_WORK_PLAN_STEP2_ERROR_DUPLICATE_EXCESS.md).  
**EA-35 / PostgreSQL re-performance: IN PROGRESS / NOT LOCKED.**  
**Overall production FINAL LOCK: NOT GRANTED.**

No architectural change is authorized merely because a test or detector finds a discrepancy. Uncertain findings must remain HOLD/OPEN until reviewed and approved.
