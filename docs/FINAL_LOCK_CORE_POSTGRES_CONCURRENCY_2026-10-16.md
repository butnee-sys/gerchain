# FINAL LOCK — CORE / PostgreSQL Concurrency Gates

**Decision:** FINAL LOCK  
**Decision date:** 2026-10-16  
**Repository:** `butnee-sys/gerchain`  
**Scope:** Canonical CORE foundation and PostgreSQL concurrency gates only.

## 1. Final decision

The repeated cycle of re-discovering already corrected findings is closed. The PostgreSQL concurrency gate and CORE gates are accepted as GREEN based on the completed SHA-level validation and correction cycle reported for this work. This record is the controlling decision to stop reopening those gates without new, concrete regression evidence.

**FINAL LOCK means the accepted implementation and its validated gates are frozen.** It does not authorize unreviewed changes to the canonical architecture, value authority, transaction boundaries, or evidence requirements.

## 2. Scope exclusions

- **SHUUD is a separate application (APP)** and is outside this CORE / PostgreSQL concurrency lock.
- SHUUD must not be reintroduced into CORE gate scope, EAI, or the canonical infrastructure lock merely because it exists in the repository.
- Product/application work is not a reason to reopen the locked CORE gates.
- EAI (Escrow as Infrastructure) is a conceptual/infrastructure principle, not a new engine or a reason to duplicate escrow, ledger, witness, or authority.

## 3. Frozen invariants

1. PostgreSQL transaction correctness and concurrency behavior remain protected.
2. Canonical Ledger remains the sole authoritative production value-movement boundary.
3. A value movement and its required escrow transition, witness, idempotency, and outbox evidence must obey the established atomicity contract.
4. No production fallback to in-memory or legacy value authority is allowed.
5. No duplicate authoritative Ledger, Escrow Engine, Witness Chain, or Outbox is allowed.
6. Decision → Authorization → Release remains mandatory.
7. Unknown or unverified conditions do not become implicit approval.
8. No architecture or gate is reopened without a specific reproducible regression, a changed requirement, or a formally approved architecture-change proposal.

## 4. Change-control rule

Any future issue must include:
- exact commit SHA;
- exact failing command or CI run;
- reproducible failure output;
- proof that the failure is within this lock's scope;
- minimal corrective change and regression test.

A previously corrected issue, an unverified suspicion, a different branch's result, or an application-layer concern is not sufficient grounds to reopen the lock.

## 5. Evidence integrity

This record does not invent CI run IDs or claim a fresh test execution that is not attached to this commit. The SHA-level validation referenced in the decision must remain linked to its original evidence. If an exact tested SHA differs from the current implementation SHA, the difference must be recorded as provenance—not used as an excuse to restart the completed gate cycle without a concrete regression.

## 6. Status

**CORE / PostgreSQL concurrency gates: FINAL LOCK — CLOSED.**

No further routine re-audit of these gates is authorized. Only the change-control conditions in Section 4 may reopen them.
