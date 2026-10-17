# FINAL LOCK — Fundamental Digital Economy Infrastructure

**Record type:** Final architecture and boundary lock  
**Repository:** `butnee-sys/gerchain`  
**Applies to:** Canonical DE/DEE/G-3/NEF/GerChain infrastructure and EAI principle  
**SHUUD:** Explicitly excluded and fully isolated  
**Operational production status:** NOT LOCKED — see mandatory evidence gates below

## 1. Final decision

The canonical architecture and its boundaries are frozen. No implementation may introduce a new canonical layer, second authoritative value store, alternate witness authority, bypass adapter, or application-owned infrastructure truth without an explicitly approved architecture-change proposal.

This document **does not falsely certify operational production readiness**. The architecture is locked; the production implementation can only be locked after the exact-SHA PostgreSQL, CI, recovery, security/governance, and independent re-performance evidence is retained and reviewed.

## 2. Canonical architecture — immutable

```text
DE
→ DE Adapter
→ DEE
→ DEE ↔ G-3 Adapter
→ G-3 Escrow Foundation
→ G-3 ↔ CORE Adapter
→ NEF + GerChain Core Infrastructure
→ CORE ↔ EXIM Adapter
→ EXIM Port
→ EXIM ↔ I2B Adapter
→ I2B
→ I2B ↔ Multi-Connector Adapter
→ State / Company / Person
→ Digital Economy Activities
```

- **DE** is the top-level Digital Economy space.
- **DEE** is the ecosystem governance, protection, trust, policy, security, and coordination environment.
- **G-3** owns escrow conditions and governance policy; it is not a third operational value engine.
- **NEF** is authoritative for asset registration, valuation, and verification truth.
- **GerChain** is authoritative for operational asset value-flow truth.
- **EXIM Port** is the external-system boundary; **I2B** is the business gateway.
- Every adjacent layer connection must use its explicit adapter.
- New products must use the existing core and must not redesign or duplicate it.

## 3. EAI — Escrow as Infrastructure

**EAI means ESCROW AS INFRASTRUCTURE.** It is a governing architectural principle, not a new architecture layer, not G-3 itself, not GerChain, not the GerChain Escrow Engine, and not CORE.

- G1: Escrow as Tool
- G2: Escrow as Service
- G3: Escrow as Infrastructure

Escrow is an infrastructure for condition-governed value movement. Value movement is permitted only when the authoritative truth, condition, authority, execution, and evidence are aligned and verifiable.

**Trust = Verified alignment of Truth, Condition, Authority, Execution, and Evidence.**

Mandatory execution sequence:

```text
Decision → Authorization → Release
```

No direct release is permitted.

## 4. Protected infrastructure invariant

**NO DOWNSTREAM ACTOR MAY ALTER THE AUTHORITATIVE TRUTH, AUTHORITY, POLICY, OR CORE EXECUTION STATE OF THE PROTECTED INFRASTRUCTURE DIRECTLY.**

Downstream requests may cross only a controlled interface, be validated, authorized, and receive a service/result. Requests to mutate protected truth, policy, authority, or core mechanisms directly must be denied.

## 5. SHUUD — complete isolation

SHUUD is outside this fundamental architecture and outside this production-readiness determination.

- SHUUD is not a core layer, core engine, value authority, production entrypoint, or evidence source for core production readiness.
- Its only published integration boundary is EXIM Port.
- SHUUD must not import canonical GerChain core/services/architecture internals or place SHUUD service modules in canonical `services/`.
- SHUUD deployment and sandbox remain separately composed.
- No SHUUD feature work or product-layer expansion is authorized by this lock record.
- The core production gate must be executed and evidenced independently of SHUUD.

## 6. Non-negotiable infrastructure invariants

1. One authoritative Canonical Ledger for production balances and movements.
2. No second Escrow Engine or second authoritative Witness Chain.
3. No application-owned infrastructure truth.
4. Every value movement is transaction-aware and idempotent.
5. Same idempotency key + same request replays; same key + different request conflicts.
6. Decision, Authorization, Release, Settlement, and Reconciliation remain distinct responsibilities.
7. Database-level atomicity for value movement, escrow transition, witness, idempotency, and outbox evidence.
8. Recovery cannot duplicate value movement.
9. Unknown or unresolved required conditions fail closed.
10. Balance equality alone is not proof of value-truth equality.
11. Witness evidence and audit records are distinct and neither may silently replace the other.
12. Legacy/in-memory/SQLite value stores must not become production authorities through fallback.
13. Schema migrations must be versioned, validated, and fail closed on missing constraints or columns.
14. Architecture changes require explicit review and a new immutable lock record.

## 7. Production lock gate — still mandatory

The following are required before declaring **PRODUCTION FINAL LOCK**:

- [ ] Exact commit SHA is identified and audited.
- [ ] PostgreSQL migrations run against a real PostgreSQL instance.
- [ ] Runtime boot validates the complete schema and configured canonical escrow.
- [ ] CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ are tested on PostgreSQL.
- [ ] Atomic rollback, idempotent replay, conflicting replay, concurrency, and recovery are re-performed.
- [ ] Deep value-truth reconciliation reports no issues on clean and adversarial fixtures.
- [ ] Legacy authority and direct-mutation paths are demonstrated fail-closed.
- [ ] Exact-SHA CI results and artifacts are retained.
- [ ] Security/IAM/MFA and branch governance evidence is supplied or formally accepted as an exception by the responsible authority.
- [ ] Independent re-performance is documented.

No unchecked item may be silently promoted to GREEN. An absent CI result is **UNVERIFIED**, not PASS. This is a hard release gate, not a discretionary recommendation.

## 8. Final status

- **Canonical architecture:** FROZEN.
- **EAI architectural principle:** FROZEN.
- **SHUUD isolation boundary:** FROZEN; SHUUD excluded.
- **Operational production implementation:** IN PROGRESS / NOT LOCKED until Section 7 evidence is complete.
- **Production lock authority:** Must be based on exact-SHA retained evidence, not this document alone.

This record freezes the design and its boundaries while preventing an unsupported production-readiness claim.
