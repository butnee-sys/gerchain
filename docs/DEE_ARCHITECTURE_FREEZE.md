# DEE / G-3 / NEF / GerChain / I2B Architecture Freeze

**Status:** FROZEN — Canonical Digital Economy Architecture
**Freeze date:** 2026-09-14
**Repository:** `butnee-sys/gerchain`

## 1. Purpose

This document is the single authoritative architectural reference for the Digital Economy Ecosystem and its core value infrastructure.

The canonical architecture is:

```text
DIGITAL ECONOMY
        │
        ▼
DEE — DIGITAL ECONOMY ECOSYSTEM
        │
     ADAPTER
        │
        ▼
G-3 ESCROW FOUNDATION
        │
     ADAPTER
        │
        ▼
NEF + GERCHAIN CORE INFRASTRUCTURE
        │
     ADAPTER
        │
        ▼
EXIM PORT
        │
     ADAPTER
        │
        ▼
I2B — INFRASTRUCTURE TO BUSINESS GATEWAY
        │
MULTI-CONNECTOR ADAPTER
        │
   ┌────┼────┐
   ▼    ▼    ▼
 STATE COMPANY PERSON
        │
        ▼
DIGITAL ECONOMY ACTIVITIES
```

The architecture is frozen. Implementation may be added, repaired, refactored, or moved to conform to this document, but implementation work must not silently change the architectural roles below.

## 2. DEE — Digital Economy Ecosystem

**DEE = DIGITAL ECONOMY ECOSYSTEM.**

DEE is the ecosystem-level governance, protection, trust, policy, security, and coordination environment. Existing governance and protection mechanisms already preserved in the repository belong to DEE and must not be duplicated unnecessarily in lower layers.

DEE includes, as applicable:

- Governance
- Policy
- Protection
- Trust framework
- Identity
- Access control
- Authorization policy
- Security
- Compliance
- Risk control
- Audit policy
- Data governance
- Recovery policy
- Interoperability
- Ecosystem-level rules and safeguards

DEE answers:

> **HOW IS THE DIGITAL ECONOMY ECOSYSTEM GOVERNED AND PROTECTED?**

DEE is an ecosystem layer, not a duplicate operational ledger, money, escrow, or settlement engine.

## 3. Adapter Principle

Adapters are explicit architectural boundaries. A layer must not bypass its defined adapter boundary to reach another layer's internal implementation.

Canonical path:

```text
DE
→ ADAPTER
→ DEE
→ ADAPTER
→ G-3
→ ADAPTER
→ NEF + GERCHAIN CORE
→ ADAPTER
→ EXIM PORT
→ ADAPTER
→ I2B GATEWAY
→ MULTI-CONNECTOR ADAPTER
→ STATE / COMPANY / PERSON
→ DIGITAL ECONOMY ACTIVITIES
```

Adapters isolate contracts, credentials, authorization, external dependencies, and implementation details.

## 4. G-3 Escrow Foundation

G-3 is the foundation for escrow as infrastructure.

G-3 contains:

1. **Condition Policy** — what must be true before value may move.
2. **Escrow Policy** — allowed escrow states and transitions: lock, hold, release, partial release, refund, expiry, cancellation, dispute hold.
3. **Governance Policy** — who may decide, authorize, sign, and release, including limits and fail-closed rules.
4. **Escrow Trinity** — Trust + Transparency + Performance.

G-3 answers:

> **WHAT MUST BE TRUE FOR A CONDITIONAL VALUE FLOW?**

G-3 is **not** a second operational Escrow Engine and does not own the operational ledger, money movement, release execution, or settlement engines.

## 5. Escrow Benchmark

Escrow has three benchmark levels:

```text
G1 = ESCROW AS TOOL
G2 = ESCROW AS SERVICE
G3 = ESCROW AS INFRASTRUCTURE
```

- **G1** protects a transaction: `LOCK → CONDITION → RELEASE`.
- **G2** provides reusable escrow service.
- **G3** governs conditional value flows across assets, organizations, transactions, and applications.

**G3 is the target architecture.**

## 6. NEF — Asset Registration, Valuation and Verification

**NEF = the authoritative asset/wealth foundation.**

NEF's locked role is:

```text
NEF
=
ХӨРӨНГИЙН БҮРТГЭЛ
+
ҮНЭЛГЭЭ
+
БАТАЛГААЖУУЛАЛТ
```

NEF owns authoritative asset truth, including:

1. Asset Registry
2. Asset Identity
3. Ownership and Rights
4. Valuation
5. Asset State
6. Asset Evidence
7. Asset Lifecycle
8. Collateral / Encumbrance
9. Verification / validation linkage
10. NEF Audit
11. NEF Recovery

NEF answers:

> **ЭНЭ ЯМАР ХӨРӨНГӨ ВЭ? ХЭНИЙХ ВЭ? ЯМАР ЭРХТЭЙ ВЭ? ЯМАР ҮНЭ ЦЭНТЭЙ ВЭ? БАТАЛГААТАЙ ЮУ?**

NEF does not become the operational money or value-flow ledger.

## 7. GerChain — All Asset Value Flows

**GerChain = the operational infrastructure for all types of asset value flows.**

The locked role is:

```text
GERCHAIN
=
ХӨРӨНГИЙН БҮХ ТӨРЛИЙН УРСГАЛ
```

This includes, as applicable:

- ownership/right transfer flows;
- sale and purchase flows;
- lease flows;
- collateral and financing flows;
- escrow flows;
- investment flows;
- payment flows;
- return/yield flows;
- distribution flows;
- refund flows;
- settlement flows;
- conditional value flows;
- other governed asset-related value flows.

GerChain operational engines include:

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

> **БАТАЛГААЖСАН ХӨРӨНГИЙН ҮНЭ ЦЭНИЙН УРСГАЛ ХЭРХЭН ЯВАХ ВЭ, ЯМАР ЭРХИЙН ДАГУУ ЯВАХ ВЭ, ЭЦСИЙН ҮР ДҮН ЮУ ВЭ?**

GerChain does not become the authoritative asset registry.

## 8. NEF + GerChain Core Infrastructure

NEF and GerChain form the core infrastructure as two complementary truths:

```text
NEF
=
ASSET TRUTH
=
БҮРТГЭЛ + ҮНЭЛГЭЭ + БАТАЛГААЖУУЛАЛТ

GERCHAIN
=
ASSET VALUE-FLOW TRUTH
=
ХӨРӨНГИЙН БҮХ ТӨРЛИЙН УРСГАЛ
```

Therefore:

> **NEF хөрөнгийг бүртгэнэ, үнэлнэ, баталгаажуулна. GerChain баталгаатай хөрөнгийн үнэ цэнийн бүх төрлийн урсгалыг удирдана.**

## 9. Escrow Trinity

Escrow Trinity is a cross-cutting invariant, not a fourth engine and not a new duplicate architecture layer.

```text
TRUST + TRANSPARENCY + PERFORMANCE
                 ↓
            RELEASE GATE
```

### TRUST — Итгэл

Answers:

> **WHO / AUTH — Хэн? Ямар эрхээр?**

### TRANSPARENCY — Ил тод байдал

Answers:

> **WHAT / PROOF — Юу болсон? Ямар нотолгоотой? Хэн гэрчилсэн?**

### PERFORMANCE — Гүйцэтгэл

Answers:

> **DID / RESULT — Ямар үр дүн гарсан?**

Release invariant:

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

## 10. Canonical Operational Lifecycle

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

## 11. Engine Boundaries

### Escrow Engine ≠ Decision Engine

- Escrow Engine executes escrow mechanics.
- Decision Engine evaluates whether release conditions are satisfied.

### Decision Engine ≠ Authorization Engine

- Decision Engine answers: **May this action proceed under the conditions?**
- Authorization Engine answers: **Is this actor/credential/policy authorized to perform it?**

### Authorization Engine ≠ Release Engine

- Authorization validates the governed permission.
- Release executes only an authorized release.

### Release Engine ≠ Settlement Engine

- Release performs governed release.
- Settlement finalizes the resulting value state.

### Settlement Engine ≠ Reconciliation Engine

- Settlement finalizes the transaction.
- Reconciliation verifies expected versus actual state.

## 12. EXIM Port

EXIM Port is the external-system boundary between the core infrastructure and external institutional or system environments.

```text
NEF + GERCHAIN CORE
        ↓
     ADAPTER
        ↓
    EXIM PORT
        ↓
     ADAPTER
```

External systems must not bypass the port boundary to reach core internals.

## 13. I2B — Infrastructure to Business Gateway

I2B means **Infrastructure to Business**.

I2B converts governed infrastructure capabilities into reusable business activity interfaces without moving authoritative truth into applications.

```text
CORE INFRASTRUCTURE
        ↓
    EXIM PORT
        ↓
  I2B GATEWAY
        ↓
BUSINESS ACTIVITY
```

## 14. Multi-Connector Adapter

I2B connects the core ecosystem to the principal economic actors through a multi-connector boundary:

```text
                 I2B GATEWAY
                      │
             MULTI-CONNECTOR ADAPTER
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     STATE          COMPANY         PERSON
       │              │              │
       └──────────────┼──────────────┘
                      ▼
           DIGITAL ECONOMY ACTIVITIES
```

State, companies, and persons consume the infrastructure through defined connectors and do not create parallel authoritative infrastructure truth.

## 15. Application and Activity Rule

Applications and digital economy activities sit outside the core infrastructure.

They may consume:

- NEF asset registration/valuation/verification;
- GerChain value-flow capabilities;
- G-3 escrow rules;
- DEE governance and protection policies;
- EXIM ports;
- I2B gateways.

They must not bypass governed core paths or create competing authoritative ledgers, witness chains, escrow truth, release truth, or asset registries.

## 16. Hard Rules

1. **No direct release.** All value release must pass Decision → Authorization → Release.
2. **No second Escrow Engine.** G-3 does not duplicate GerChain's operational Escrow Engine.
3. **No second authoritative Witness Chain.** Existing witness infrastructure remains authoritative.
4. **No second authoritative Ledger.** Existing GerChain ledger remains authoritative for value-flow records.
5. **No application-owned infrastructure truth.** Applications cannot create competing authoritative escrow, release, settlement, ledger, or asset truth.
6. **Trust, Transparency, and Performance are mandatory release conditions.**
7. **Unknown is not pass.** Any unresolved required condition results in deny/hold.
8. **Database-level atomicity is mandatory for one-time release invariants.**
9. **Outbox processing must support lease/recovery semantics where asynchronous delivery is used.**
10. **Recovery must not create duplicate value movement.**
11. **NEF remains authoritative for asset registration, valuation, and verification truth.**
12. **GerChain remains authoritative for operational asset value-flow truth.**
13. **G-3 defines escrow conditions and governance; it does not become a third operational core.**
14. **DEE governs and protects the ecosystem; it does not duplicate lower-level operational engines.**
15. **EXIM is the external boundary. External systems do not bypass it.**
16. **I2B is the infrastructure-to-business gateway.**
17. **Adapters are mandatory architectural boundaries where shown in the canonical path.**
18. **New products may use the core without redesigning the core.**
19. **Implementation changes must conform to this document unless an explicit architecture-change proposal is approved.**

## 17. Change Governance

This document is the canonical architecture.

A normal feature, bug fix, test, refactor, database migration, connector, application change, or implementation repair must not silently change the architecture.

An architecture change requires an explicit proposal identifying:

- the rule being changed;
- the affected boundary;
- why the current boundary is insufficient;
- migration impact;
- compatibility impact;
- tests required;
- approval before implementation.

Until such an explicit architecture change is approved, this document remains the source of truth.
