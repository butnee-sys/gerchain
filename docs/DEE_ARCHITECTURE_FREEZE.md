# DE / DEE / G-3 / NEF / GerChain / EXIM / I2B Architecture Freeze

**Status:** FROZEN — Canonical Digital Economy Architecture
**Freeze date:** 2026-09-14
**Repository:** `butnee-sys/gerchain`

## 1. Purpose and top-level DE

This document is the single authoritative architectural reference for the Digital Economy and its core value infrastructure.

**DE = DIGITAL ECONOMY** and is the mandatory top-level economic space. DE is not an optional heading and must not be bypassed. Future international digital-economy connections may attach at the DE level without changing the NEF + GerChain core.

The locked architecture is:

```text
DE — DIGITAL ECONOMY
 │
 ▼
DE ADAPTER
 │
 ▼
DEE — DIGITAL ECONOMY ECOSYSTEM
 │
 ▼
DEE ↔ G-3 ADAPTER
 │
 ▼
G-3 ESCROW FOUNDATION
 │
 ▼
G-3 ↔ CORE ADAPTER
 │
 ▼
NEF + GERCHAIN CORE INFRASTRUCTURE
 │
 ▼
CORE ↔ EXIM ADAPTER
 │
 ▼
EXIM PORT
 │
 ▼
EXIM ↔ I2B ADAPTER
 │
 ▼
I2B — INFRASTRUCTURE TO BUSINESS
 │
 ▼
I2B ↔ MULTI-CONNECTOR ADAPTER
 │
 ▼
MULTI-CONNECTOR
 ├── STATE
 ├── COMPANY
 └── PERSON
 │
 ▼
DIGITAL ECONOMY ACTIVITIES
```

**DE and EXIM are different boundaries:**

- **DE** is the top-level Digital Economy space and future international connection level.
- **EXIM Port** is the core infrastructure boundary for external institutional/system environments.
- EXIM must not be treated as a replacement for DE or as the international DE boundary.

The architecture is frozen. Implementation may be added, repaired, refactored, or moved only to conform to this document unless an explicit architecture-change proposal is approved.

## 2. Adapter principle

Every layer-to-layer connection shown in the canonical path is an explicit adapter boundary.

Adapters provide contract translation, authorization/context propagation, boundary validation, and dependency isolation. They do **not** create new authoritative truth or duplicate operational engines.

Locked adapter sequence:

```text
DE
→ DE Adapter
→ DEE
→ DEE ↔ G-3 Adapter
→ G-3
→ G-3 ↔ Core Adapter
→ NEF + GerChain Core
→ Core ↔ EXIM Adapter
→ EXIM Port
→ EXIM ↔ I2B Adapter
→ I2B
→ I2B ↔ Multi-Connector Adapter
→ State / Company / Person
→ Digital Economy Activities
```

No layer may bypass its defined adapter boundary to reach another layer's internal implementation.

## 3. DEE — Digital Economy Ecosystem

**DEE = DIGITAL ECONOMY ECOSYSTEM.**

DEE is the ecosystem-level governance, protection, trust, policy, security, and coordination environment.

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

DEE is not a duplicate operational ledger, money, escrow, release, or settlement engine.

## 4. G-3 Escrow Foundation

G-3 is the foundation for escrow as infrastructure.

G-3 contains:

1. **Condition Policy** — what must be true before value may move.
2. **Escrow Policy** — allowed escrow states and transitions.
3. **Governance Policy** — who may decide, authorize, sign, and release, including limits and fail-closed rules.
4. **Escrow Trinity** — Trust + Transparency + Performance.

G-3 answers:

> **WHAT MUST BE TRUE FOR A CONDITIONAL VALUE FLOW?**

G-3 is **not** a second operational Escrow Engine and does not own operational ledger, money movement, release execution, or settlement engines.

### Escrow benchmark

```text
G1 = ESCROW AS TOOL
G2 = ESCROW AS SERVICE
G3 = ESCROW AS INFRASTRUCTURE
```

- G1 protects a transaction: `LOCK → CONDITION → RELEASE`.
- G2 provides reusable escrow service.
- G3 governs conditional value flows across assets, organizations, transactions, and applications.

## 5. NEF — Asset Registration, Valuation and Verification

**NEF = ХӨРӨНГИЙН БҮРТГЭЛ + ҮНЭЛГЭЭ + БАТАЛГААЖУУЛАЛТ.**

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

> **ЭНЭ ЯМАР ХӨРӨНГӨ ВЭ? ХЭНИЙХ ВЭ? ЯМАР ЭРХТЭЙ ВЭ? ЯМАР ҮНЭ ЦЭНЭТЭЙ ВЭ? БАТАЛГААТАЙ ЮУ?**

NEF does not become the operational money or value-flow ledger.

## 6. GerChain — All Asset Value Flows

**GerChain = ХӨРӨНГИЙН БҮХ ТӨРЛИЙН УРСГАЛ.**

GerChain is the operational infrastructure for asset value flows, including ownership/right transfer, sale and purchase, lease, collateral, financing, escrow, investment, payment, return/yield, distribution, refund, settlement, conditional value, and other governed asset-related flows.

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

GerChain does not become the authoritative asset registry.

## 7. NEF + GerChain Core

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

> **NEF хөрөнгийг бүртгэнэ, үнэлнэ, баталгаажуулна. GerChain баталгаатай хөрөнгийн үнэ цэнийн бүх төрлийн урсгалыг удирдана.**

## 8. Escrow Trinity

```text
TRUST + TRANSPARENCY + PERFORMANCE
                 ↓
            RELEASE GATE
```

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

The system is **fail-closed**. Trust answers who/authority, Transparency answers proof/evidence, and Performance answers result/outcome.

## 9. Canonical operational lifecycle

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

## 10. Engine boundaries

- Escrow Engine ≠ Decision Engine.
- Decision Engine ≠ Authorization Engine.
- Authorization Engine ≠ Release Engine.
- Release Engine ≠ Settlement Engine.
- Settlement Engine ≠ Reconciliation Engine.
- No second Escrow Engine.
- No second authoritative Witness Chain.
- No second authoritative Ledger.
- No direct release.

All release follows:

```text
DECISION → AUTHORIZATION → RELEASE
```

## 11. EXIM Port

EXIM Port is the external-system boundary between NEF + GerChain core infrastructure and external institutional/system environments.

```text
NEF + GERCHAIN CORE
        ↓
CORE ↔ EXIM ADAPTER
        ↓
    EXIM PORT
        ↓
EXIM ↔ I2B ADAPTER
```

External systems must not bypass EXIM to reach core internals.

## 12. I2B — Infrastructure to Business

I2B converts governed infrastructure capabilities into reusable business activity interfaces without moving authoritative truth into applications.

```text
CORE → EXIM → I2B → BUSINESS ACTIVITY
```

## 13. Multi-Connector Adapter

```text
                 I2B
                  │
       I2B ↔ MULTI-CONNECTOR ADAPTER
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     STATE      COMPANY     PERSON
       └──────────┼──────────┘
                  ▼
       DIGITAL ECONOMY ACTIVITIES
```

State, companies, and persons consume the infrastructure through defined connectors and do not create parallel authoritative infrastructure truth.

## 14. Application and activity rule

Applications and Digital Economy Activities sit outside the core infrastructure. They may consume governed NEF, GerChain, G-3, DEE, EXIM, and I2B capabilities but must not bypass the canonical path or create competing authoritative ledgers, witness chains, escrow truth, release truth, settlement truth, or asset registries.

Existing `nef_gerchain_port` remains compatible with this architecture and may be refactored behind the canonical adapters; it must not be used to bypass them.

## 15. Hard rules

1. **DE is mandatory and top-level.**
2. **DE is distinct from EXIM.** DE is the top-level Digital Economy space; EXIM is the core external-system boundary.
3. **Every shown layer-to-layer connection uses an explicit adapter.**
4. **No direct release.** Decision → Authorization → Release is mandatory.
5. **No second Escrow Engine.** G-3 does not duplicate GerChain's operational Escrow Engine.
6. **No second authoritative Witness Chain.**
7. **No second authoritative Ledger.**
8. **No application-owned infrastructure truth.**
9. **Trust, Transparency, and Performance are mandatory release conditions.**
10. **Unknown is not pass.** Required unresolved conditions result in deny/hold.
11. **Database-level atomicity is mandatory for one-time release invariants.**
12. **Outbox processing must support lease/recovery semantics where asynchronous delivery is used.**
13. **Recovery must not create duplicate value movement.**
14. **NEF remains authoritative for asset registration, valuation, and verification truth.**
15. **GerChain remains authoritative for operational asset value-flow truth.**
16. **G-3 defines escrow conditions and governance; it does not become a third operational core.**
17. **DEE governs and protects the ecosystem; it does not duplicate lower-level operational engines.**
18. **EXIM is the external boundary. External systems do not bypass it.**
19. **I2B is the infrastructure-to-business gateway.**
20. **New products may use the core without redesigning the core.**
21. **Implementation changes must conform to this document unless an explicit architecture-change proposal is approved.**

## 16. Change governance

This document is the canonical architecture. A normal feature, bug fix, test, refactor, database migration, connector, application change, or implementation repair must not silently change the architecture.

An architecture change requires an explicit proposal identifying:

- the rule being changed;
- the affected boundary;
- why the current boundary is insufficient;
- migration impact;
- compatibility impact;
- tests required;
- approval before implementation.

Until such an explicit architecture change is approved, this document remains the source of truth.
