# Production Readiness Closure Register — Gates 4–7

**Status:** IN PROGRESS / NOT LOCKED  
**Scope:** Fundamental architecture + EAI; CORE is one infrastructure, not the whole target. Product-layer work remains out of scope until EAI is production-ready and locked.  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Updated:** 2026-10-21

This register is an evidence ledger, not a declaration of success. A gate closes only when its technical and assurance criteria are evidenced against an identified commit. Historical evidence is not silently promoted to current branch-tip evidence.

## Execution order

4. Authority  
5. CORE  
6. Adapter boundaries  
7. EAI / G3

Each gate is evaluated independently. Closing one does not imply the next is closed.

---

## Gate 4 — Authority

**Disposition: PARTIAL — NOT CLOSED**

### Verified implementation evidence
- Production runtime factory configures the Canonical Ledger authority.
- Runtime startup applies the versioned PostgreSQL migration chain and runs a canonical schema guard.
- Production startup fails closed when the database is not PostgreSQL, required schema elements are missing, critical unique keys are absent, or the escrow lifecycle CHECK constraint is not canonical.
- Canonical balance/movement authority is defined as `gerchain_ledger_accounts` and `gerchain_ledger_movements`.
- Legacy authority freeze is documented in `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md`.
- Legacy API/UI value mutation bypasses were changed to fail closed, as documented in `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md`.

### Remaining closure criteria
- Prove the supported upgrade path from the actual prior production schema, not only clean-database initialization.
- Verify every production entrypoint and deployment profile fails closed instead of falling back to `MoneyLedger`, `ReleaseAccount`, `AccountBalance`, or SQLite.
- Physically archive/remove or technically disable all legacy authoritative stores only after a reversible, evidence-backed migration plan.
- Reconcile full movement history, source/destination, operation, escrow, witness, outbox, idempotency, and integrity hashes.
- Attach current exact-SHA CI and independent re-performance evidence.

**Exit rule:** no unexplained value-truth mismatch; exactly one production value authority; no writable legacy authority reachable from production.

---

## Gate 5 — CORE

**Disposition: TECHNICAL BASELINE DOCUMENTED; FORMAL ASSURANCE OPEN**

### Existing evidence register
- `docs/CORE_AUDIT_LOCK_STATUS.md`
- `docs/CORE_CONTROL_MATRIX.md`
- `docs/CORE_AUDIT_EVIDENCE_INDEX.md`
- Frozen PwC baseline remains immutable.

### Open controls that cannot be inferred from source code
- Organizational IAM/MFA and privileged-access review evidence.
- Main-branch protection/ruleset and required-review governance evidence.
- Required post-merge CI for the exact audited commit.
- Final independent audit/re-performance package and explicit exception acceptance, if applicable.

**Exit rule:** all required technical controls and organizational controls are either evidenced closed or formally accepted as named audit exceptions by the responsible authority. No missing evidence is relabelled GREEN.

---

## Gate 6 — Adapter boundaries

**Disposition: IMPLEMENTED STRUCTURE; CONTRACT CLOSURE OPEN**

### Architecture surfaces to verify
- `architecture/composition_root.py`
- `architecture/governed_flow_adapters.py`
- `architecture/boundary_adapters.py`
- `architecture/g3_core.py`
- `architecture/ports.py`
- `architecture/nef_gerchain.py`

The frozen architecture requires an explicit adapter for every layer-to-layer connection. Adapters must preserve fail-closed semantics and may not create a parallel authority.

### Required contract tests
1. Missing/invalid boundary identity is denied.
2. Unknown required condition is denied/held, never treated as PASS.
3. A downstream request cannot mutate protected truth, policy, authority, or core execution state.
4. A request cannot bypass Decision → Authorization → Release.
5. No adapter creates a second Ledger, Escrow Engine, Witness Chain, or authoritative Outbox.
6. Invalid NEF asset/valuation/verification evidence is denied.
7. Adapter failure cannot silently fall back to a memory/SQLite runtime.
8. Contract tests run on the exact candidate commit and are included in required CI.

**Exit rule:** all adapter contract tests pass and the tests demonstrate both allowed service flow and denied infrastructure mutation.

---

## Gate 7 — EAI / G3

**Disposition: HISTORICAL POSTGRESQL PROOF RECORDED; CURRENT UNIFIED LOCK OPEN**

### Frozen conceptual separation
- EAI = Escrow as Infrastructure; it is an architectural principle, not a new architecture layer.
- G3 = Escrow Foundation / condition and governance policy implementation.
- G3 is not the Canonical Ledger, not the GerChain Escrow Engine, and not a third operational core.
- Trust + Transparency + Performance are mandatory release conditions.
- Value movement must follow Decision → Authorization → Release.
- EAI must use the same canonical Ledger, Witness, Outbox, idempotency, reconciliation and recovery paths as the rest of the production runtime.

### Historical evidence recorded
`docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md` records successful PostgreSQL production, EAI, and independent persisted-value runs on commit `f11fcb6411f1458c7bb4696566a695a52141b0c3`.

That evidence is valid for the recorded execution SHA only. It is not proof that every required workflow passed on the current branch tip.

### Remaining closure criteria
- Re-run EAI PostgreSQL proof on the exact release candidate SHA.
- Prove all three Trinity conditions fail closed independently.
- Prove decision denial, authorization denial, unknown evidence, stale/replayed request, and integrity mismatch cannot move value.
- Prove EAI does not create a second Ledger, Witness Chain, Outbox, or release authority.
- Prove process interruption/restart and idempotent replay cannot duplicate movement.
- Bind the EAI proof, production PostgreSQL proof, deep reconciliation, required CI, security scan, and independent re-performance to the same exact SHA.

**Exit rule:** the EAI-specific proof and all required shared infrastructure gates pass on one exact SHA; no unresolved authority or evidence mismatch remains.

---

## Release lock rule

The fundamental architecture is not production-locked until Gates 4, 5, 6, and 7 are individually closed or their remaining exceptions are formally accepted by the responsible authority. Product layers remain excluded until that lock is explicit.

**Current overall disposition: IN PROGRESS / NOT LOCKED.**
