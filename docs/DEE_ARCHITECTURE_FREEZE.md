# G-3 / NEF / GerChain Core Architecture Freeze

**Status:** FROZEN — Canonical Core Architecture
**Freeze date:** 2026-09-14
**Repository:** `butnee-sys/gerchain`

## 1. Purpose

This document is the single authoritative architectural reference for the core value infrastructure of `butnee-sys/gerchain`.

The frozen core consists of:

- **G-3 Escrow Foundation** — conditional-value rules, escrow policy, governance policy, and the operating principle of Escrow Trinity.
- **NEF** — Asset Truth; asset and wealth registration, identity, rights, valuation, state, evidence, and encumbrance truth.
- **GerChain** — Value-Flow Truth; ledger, money, escrow execution, witness, verification, decision, authorization, release, settlement, reconciliation, audit, consensus, and recovery.
- **SHUUD/SHIID and other products** — application layer only; never core infrastructure.

International architecture and cross-border ports are explicitly **out of scope for this freeze**. They must not be used to redefine the core.

The architecture is frozen. Implementation may be added, repaired, refactored, or moved to conform to this document, but implementation work must not silently change the architectural roles below.

## 2. Escrow Benchmark

Escrow has three benchmark levels:

```text
G1 = ESCROW AS TOOL
G2 = ESCROW AS SERVICE
G3 = ESCROW AS INFRASTRUCTURE
```

### G1 — Escrow as Tool

Escrow is a transaction tool:

```text
LOCK → CONDITION → RELEASE
```

### G2 — Escrow as Service

Escrow is delivered as a reusable service to multiple users and transactions.

### G3 — Escrow as Infrastructure

Escrow becomes infrastructure for governing conditional value flows across assets, organizations, transactions, and applications.

**G3 is the target architecture of this repository.**

## 3. Canonical Core Architecture

```text
                    G-3 ESCROW FOUNDATION
                 ESCROW AS INFRASTRUCTURE
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
           NEF                       GERCHAIN
      ASSET TRUTH                VALUE-FLOW TRUTH
             │                           │
     ┌───────┼────────┐        ┌─────────┼──────────┐
     │       │        │        │         │          │
  Identity Rights  Valuation  Ledger    Money     Escrow
     │       │        │        │         │          │
  State  Evidence Encumbrance │         │          │
     │       │        │        └─────────┼──────────┘
     └───────┼────────┘                  │
             │                           │
             └────────────┬──────────────┘
                          ▼
                    ESCROW TRINITY
              ┌───────────┼───────────┐
              ▼           ▼           ▼
            TRUST    TRANSPARENCY  PERFORMANCE
              │           │           │
              └───────────┼───────────┘
                          ▼
                    DECISION ENGINE
                          ▼
                  AUTHORIZATION ENGINE
                          ▼
                     RELEASE ENGINE
                          ▼
                   SETTLEMENT ENGINE
                          ▼
                RECONCILIATION ENGINE
                          ▼
                      AUDIT / RECOVERY
                          ▼
                       COMPLETE
```

## 4. Architectural Roles

### G-3 Escrow Foundation

G-3 is **not** a second operational engine layer and is **not** GerChain's Escrow Engine.

G-3 contains the governing definitions and policies:

1. **Condition Policy** — what must be true before value may move.
2. **Escrow Policy** — allowed escrow states and transitions: lock, hold, release, partial release, refund, expiry, cancellation, dispute hold.
3. **Governance Policy** — who may decide, authorize, sign, and release, including limits and fail-closed rules.
4. **Escrow Trinity** — the mandatory operating principle.

G-3 answers:

> **WHAT MUST BE TRUE?**

G-3 does not own the operational ledger, money movement, release execution, or settlement engines.

### NEF — Asset Truth

NEF owns the authoritative truth about assets and wealth:

1. Asset Registry
2. Asset Identity
3. Ownership and Rights
4. Valuation
5. Asset State
6. Asset Evidence
7. Asset Lifecycle
8. Collateral / Encumbrance
9. NEF Audit
10. NEF Recovery

NEF answers:

> **WHAT ASSET IS THIS, WHO HAS WHAT RIGHTS, AND WHAT IS ITS VALID VALUE/STATE?**

### GerChain — Value-Flow Truth

GerChain owns operational conditional value flow:

1. Ledger Engine
2. Money Engine
3. Escrow Engine
4. Witness Engine
5. Verification Engine
6. Decision Engine
7. Authorization Engine
8. Release Engine
9. Settlement Engine
10. Reconciliation Engine
11. Audit Engine
12. Consensus Engine
13. Recovery Engine

GerChain answers:

> **HOW DOES VERIFIED VALUE MOVE, UNDER WHAT AUTHORIZATION, AND WHAT WAS THE FINAL RESULT?**

### Application Layer

SHUUD/SHIID and future products consume the core infrastructure.

```text
APPLICATION
   ↓
APPLICATION ADAPTER
   ↓
GATEWAY / EXISTING CONNECTION BOUNDARY
   ↓
G-3 + NEF + GERCHAIN CORE
```

Applications do not own asset truth, escrow truth, authorization truth, release truth, or settlement truth.

## 5. Escrow Trinity

Escrow Trinity is a **cross-cutting invariant**, not a fourth engine and not a new architectural layer.

```text
TRUST + TRANSPARENCY + PERFORMANCE
                 ↓
            RELEASE GATE
```

### TRUST — Итгэл

Answers:

> **WHO / AUTH — Хэн? Ямар эрхээр?**

Includes existing identity, credential, authority, policy, signature, root-of-trust, and access-control mechanisms.

### TRANSPARENCY — Ил тод байдал

Answers:

> **WHAT / PROOF — Юу болсон? Ямар нотолгоотой? Хэн гэрчилсэн?**

Includes evidence, witness, witness chain, verification, event history, audit, and reconciliation.

### PERFORMANCE — Гүйцэтгэл

Answers:

> **DID / RESULT — Ямар үр дүн гарсан?**

Includes execution, escrow mechanics, release, settlement, and final state.

### Release invariant

```text
TRUST = PASS
TRANSPARENCY = PASS
PERFORMANCE = PASS
        ↓
RELEASE MAY PROCEED
```

If any required component is `FAIL` or `UNKNOWN`:

```text
RELEASE = DENY / HOLD
```

The system is **fail-closed**.

## 6. Canonical Operational Lifecycle

The core escrow lifecycle is:

```text
CREATE
→ IDENTIFY
→ AUTHORIZE
→ DEFINE CONDITIONS
→ FUND
→ LOCK
→ EXECUTE
→ COLLECT EVIDENCE
→ WITNESS
→ VERIFY
→ DECIDE
→ AUTHORIZED RELEASE / DISPUTE HOLD
→ SETTLE / RESOLVE
→ RECONCILE
→ AUDIT
→ COMPLETE
```

Not every application must expose every step to a user, but the core must preserve the governed lifecycle.

## 7. Engine Boundaries

### Escrow Engine ≠ Decision Engine

- Escrow Engine executes escrow mechanics.
- Decision Engine evaluates whether release conditions are satisfied.

### Decision Engine ≠ Authorization Engine

- Decision Engine answers: **May this action proceed under the conditions?**
- Authorization Engine answers: **Is this actor/credential/policy authorized to perform it?**

### Authorization Engine ≠ Release Engine

- Authorization Engine creates/validates the governed permission.
- Release Engine executes only an authorized release.

### Release Engine ≠ Settlement Engine

- Release Engine performs the governed release.
- Settlement Engine finalizes the resulting value state.

### Settlement Engine ≠ Reconciliation Engine

- Settlement Engine finalizes the transaction.
- Reconciliation Engine verifies expected versus actual state across the relevant records.

## 8. Hard Rules

1. **No direct release.** All value release must pass the governed Decision → Authorization → Release path.
2. **No second Escrow Engine.** G-3 does not duplicate GerChain's operational Escrow Engine.
3. **No second authoritative Witness Chain.** Existing witness infrastructure remains authoritative.
4. **No second authoritative Ledger.** Existing GerChain ledger remains authoritative for value-flow records.
5. **No application-owned infrastructure truth.** SHUUD/SHIID cannot create its own authoritative escrow, release, settlement, or ledger truth.
6. **Trust, Transparency, and Performance are mandatory release conditions.**
7. **Unknown is not pass.** Any unresolved required condition results in deny/hold.
8. **Database-level atomicity is mandatory for one-time release invariants.** Application-level thread locks are not authoritative.
9. **Outbox processing must support lease/recovery semantics where asynchronous delivery is used.**
10. **Recovery must not create duplicate value movement.**
11. **NEF remains the asset/wealth truth.** GerChain does not become the authoritative asset registry.
12. **GerChain remains the value-flow truth.** NEF does not become the operational money/escrow ledger.
13. **G-3 defines rules and governance; it does not become a third operational core.**
14. **New products may use the core without redesigning the core.**
15. **Implementation changes must conform to this document unless an explicit architecture-change proposal is approved.**

## 9. Current Repository Mapping

The current implementation already contains important parts of this architecture, including:

- `escrow/engine.py`, `escrow/state.py`, `escrow/record.py` — escrow mechanics and state.
- `money/engine.py`, `money/ledger.py`, `money/record.py` — value movement and ledger.
- `witness/chain.py`, `witness/multi.py`, `witness/independent_multi.py`, `witness/record.py` — witness infrastructure.
- `network/authorization.py`, `network/authorized_identity.py` — authorization and identity controls.
- `network/audit_pipeline.py`, `network/audit_logger.py` — audit infrastructure.
- `network/consensus.py` — consensus infrastructure.
- `network/chain_tip_recovery.py`, `network/failure.py`, `network/failure_isolation.py` — recovery/failure infrastructure.
- `network/nef_engine.py` / `network/nef_state_engine.py` — existing NEF-related state implementation.
- `core/` — canonical state/hash primitives.
- `database/` and `database.py` — persistence boundary.

These files are implementation locations, not permission to change the architectural boundaries.

## 10. Required Additions — Without Redesigning the Core

The following are additions or completion work only:

### G-3

- Condition Policy
- Escrow Policy
- Governance Policy
- Trinity evaluation contract

### NEF

- Complete asset identity/rights/valuation/state/evidence linkage where missing.
- Encumbrance/collateral truth where missing.
- NEF audit/recovery linkage where missing.

### GerChain

- Complete Trinity proof aggregation.
- Add/complete Decision Engine.
- Connect Decision → Authorization.
- Complete governed Release Engine path.
- Complete Settlement and Reconciliation.
- Preserve existing Witness, Ledger, Escrow, Audit, Consensus, and Recovery engines.

### Database / reliability

- PostgreSQL race-safe atomic release.
- One-time milestone/release database invariants.
- Concurrent schema-version protection.
- Outbox PROCESSING lease and recovery.

### Applications

- Keep SHUUD/SHIID outside the core.
- Applications call the governed core path; they do not bypass it.

## 11. Change Governance

This document is the canonical core architecture.

A normal feature, bug fix, test, refactor, database migration, or application change **must not change the architecture**.

An architecture change requires an explicit proposal that identifies:

- the rule being changed;
- the affected boundary;
- why the current boundary is insufficient;
- migration impact;
- compatibility impact;
- tests required;
- approval before implementation.

Until such an explicit architecture change is approved, this document remains the source of truth.
