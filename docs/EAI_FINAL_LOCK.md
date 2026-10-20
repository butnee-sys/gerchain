# EAI FINAL LOCK — Escrow as Infrastructure

**Status:** EAI FINAL LOCK  
**Scope:** EAI architectural contract and its canonical implementation boundary only.  
**Repository:** `butnee-sys/gerchain`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Decision:** Freeze the EAI contract. Do not reopen already-completed PostgreSQL Concurrency or CORE-gates checks solely because a workflow summary previously selected the wrong validation path. If a future run reports failure, first validate the workflow file, job, test command, commit SHA, and actual job log before attributing the result to application code.

## 1. Canonical definition

**EAI = Escrow as Infrastructure.**

EAI is an architectural principle and production assurance contract. It is not a new canonical architecture layer, not G3 itself, not GerChain, not the GerChain Escrow Engine, and not CORE.

The canonical maturity sequence is:

- **G1 — Escrow as Tool**
- **G2 — Escrow as Service**
- **G3 — Escrow as Infrastructure**

G3 is the escrow foundation that governs the conditions and infrastructure-level trust requirements. EAI names the principle that escrow is foundational economic infrastructure, not an isolated feature or service.

## 2. Locked trust invariant

**We do not move value on hope. Value moves only when structurally verified trust conditions are satisfied.**

Operational definition:

**Trust = verified alignment of Truth, Condition, Authority, Execution, and Evidence.**

Required sequence:

`Explicit Conditions → Verification → Decision → Authorization → Release → Witness/Evidence → Audit → Reconciliation`

No direct release is permitted. Decision, Authorization, and Release remain distinct responsibilities.

## 3. Canonical authority boundaries

- **NEF:** authoritative asset registration, valuation, and verification truth.
- **G3:** escrow condition, escrow policy, governance policy, and Trust + Transparency + Performance conditions.
- **GerChain Canonical Ledger:** authoritative operational balances and value movements.
- **Canonical Escrow aggregate:** authoritative durable escrow lifecycle state.
- **Witness:** evidence of committed execution; it is not a second ledger or a second authoritative witness chain.
- **Outbox:** one transaction-participating authoritative event path for committed operations.
- **Audit:** records accountability and review; audit is not a substitute for witness evidence.
- **Recovery:** repairs/reconciles execution state without creating alternate truth authority or duplicate value movement.

## 4. Mandatory invariants

1. One authoritative production Ledger balance store and movement history.
2. No production balance mutation outside the Canonical Ledger transaction boundary.
3. One durable Escrow state machine; no parallel authoritative escrow state.
4. Decision ≠ Authorization ≠ Release.
5. A release requires approved Decision, valid Authorization, verified evidence, and all G3 Trinity conditions.
6. Idempotent replay of the same request must not move value twice; reuse of a key with a different request must conflict.
7. Ledger movement, escrow transition, witness, idempotency result, and outbox event must commit or roll back together for value-moving operations.
8. Refund destination and cancellation reversal destination are derived from authoritative escrow data, not arbitrary caller input.
9. Unknown or unresolved required conditions fail closed.
10. Recovery follows **DETECT → ISOLATE → HOLD → DIAGNOSE → RECONCILE → RECOVER → VERIFY → AUDIT**. If verification fails, remain HOLD.
11. Balance equality alone is insufficient: **Balance equality ≠ Value-truth equality.**
12. Legacy/in-memory/SQLite stores are non-authoritative and must never be silently selected as production fallbacks.
13. Every production-readiness claim must identify the exact commit SHA and the successful workflow/job/test path that actually executed. A workflow-routing or test-selection defect must not be misreported as an application regression.

## 5. Production operation contract

| Operation | Required canonical behavior |
|---|---|
| CREATE | Persist the durable escrow aggregate in CREATED; no value movement |
| FUND | Canonical Ledger movement and CREATED → FUNDED atomically |
| LOCK | Durable FUNDED → LOCKED transition; state-only, no ledger movement |
| RELEASE | Verified LOCKED → RELEASED plus canonical Ledger movement atomically |
| REFUND | LOCKED → REFUNDED; destination from authoritative refund destination |
| CANCEL | CREATED → CANCELLED without movement, or reverse funded value to authoritative source |
| SETTLEMENT | Orchestration only; value movement remains in Canonical Ledger |
| BALANCE READ | Read only from Canonical Ledger |
| ESCROW READ | Read only from durable Canonical Escrow aggregate |

## 6. PDEIZ protection compatibility

EAI must conform to the PDEIZ hard invariant:

**NO DOWNSTREAM ACTOR MAY ALTER THE AUTHORITATIVE TRUTH, AUTHORITY, POLICY, OR CORE EXECUTION STATE OF PDEIZ DIRECTLY.**

Downstream requests may use controlled interfaces and validated, authorized service paths. Direct mutation of protected truth, authority, policy, or core execution state is denied.

## 7. Lock boundary

This lock freezes the **EAI definition, trust contract, authority ownership, lifecycle invariants, and production operation contract**. It does not silently claim that a live deployment has passed a new independent audit, and it does not lock unrelated product layers.

The current repository contains implementation work for canonical Ledger and Escrow paths, deep value-truth reconciliation, and production runtime construction. Runtime/deployment evidence remains tied to the exact tested commit and the actual workflow path; this document must not be used to infer an unobserved live PostgreSQL run.

## 8. Change control

Any change to the locked EAI invariants requires an explicit architecture-change proposal with:
- the invariant being changed and reason;
- affected authority boundaries and data paths;
- migration and rollback plan;
- duplicate-value-movement and replay analysis;
- tests for positive, negative, rollback, recovery, and concurrency cases;
- exact-SHA CI evidence with verified workflow/job routing;
- independent re-performance where the change affects production value authority.

Routine implementation conforming to this contract does not reopen the architecture decision.

---

**EAI architectural contract: LOCKED.**  
**Do not reopen completed PostgreSQL Concurrency or CORE-gates validation unless fresh, correctly routed evidence on the exact SHA proves a genuine failure.**