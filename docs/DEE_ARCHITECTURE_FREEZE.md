# DEE Architecture Freeze

**Status:** FROZEN — Conceptual Architecture
**Freeze date:** 2026-09-14
**Repository:** `butnee-sys/gerchain`

## 1. Purpose

This document is the canonical architectural reference for the Digital Economy (DE) / Digital Economy Ecosystem (DEE) architecture implemented and extended around G3 Escrow, NEF, GerChain, EXIM Port, Country Port, adapters, and I2B routing.

The **conceptual architecture is frozen**. Implementation may be refactored to conform to this architecture, but the architecture itself must not be changed implicitly through implementation work.

## 2. Canonical Architecture

```text
DE
↓
ADAPTER
↓
DEE = DIGITAL ECONOMY ECOSYSTEM = NATURE
↓
ADAPTER
↓
G3 ESCROW FOUNDATION
↓
ADAPTER
↓
NEF + GERCHAIN
↓
ADAPTER
↓
EXIM PORT
↓
ADAPTER
↓
DE–COUNTRY PORT
↓
INTERNATIONAL DIGITAL ECONOMY FLOW
↓
DE–COUNTRY PORT
↓
ADAPTER
↓
EXIM PORT
↓
ADAPTER
↓
I2B MULTI-CONNECTOR GATEWAY
↓
MULTI-CONNECTOR ADAPTER
↓
┌───────────────┬────────────────┬────────────────┐
│               │                │
ТӨР             КОМПАНИ          ХУВЬ ХҮН
│               │                │
ADAPTER         ADAPTER          ADAPTER
│               │                │
└───────────────┴────────────────┴────────────────┘
↓
DIGITAL ECONOMY ACTIONS
```

## 3. Architectural Definitions

- **DE — Digital Economy:** Дижитал эдийн засаг.
- **DEE — Digital Economy Ecosystem:** Дижитал эдийн засгийн экосистем; the natural ecosystem context of the digital economy.
- **G3 Escrow Foundation:** protected foundational infrastructure for conditional value movement.
- **NEF:** Asset & Wealth Infrastructure — хөрөнгө, баялгийн бүртгэл, үнэлгээний суурь дэд бүтэц.
- **GerChain:** Value & Flow Infrastructure — нөхцөлт хадгаламжид суурилсан үнэ цэнийн урсгалын дэд бүтэц.
- **EXIM Port:** Inbound-Outbound Port — CORE-ийн гадагш/дотогш чиглэсэн урсгалын үндсэн зохицуулагч.
- **DE–Country Port:** Cross-border Digital Economy Port — улс хоорондын дижитал эдийн засгийн урсгалын хил, бүрэн эрх, зохицуулалтын боомт.
- **Adapter:** Actual system connection implementation — бодит систем хоорондын холболтын хэрэгжүүлэлт.
- **I2B Gateway:** Infrastructure-to-Business Gateway — холбогчийг сонгох, чиглүүлэх, удирдах дэд бүтэц-үйл ажиллагааны чиглүүлэгч.
- **Multi-Connector Adapter:** төр, компани, хувь хүний холболтын зангилаа.
- **TRINITY:** TRUST + TRANSPARENCY + PERFORMANCE; a cross-cutting architectural invariant, not a separate layer or engine.

## 4. Hard Architectural Rules

1. **No direct external access to CORE.**
2. **CORE external inbound/outbound flow is governed only through EXIM Port.**
3. **No application may directly depend on NEF or GerChain engines.**
4. **All real external system connections are implemented through Adapters.**
5. **I2B Gateway is a routing/selection layer, not the connector itself.**
6. **Multi-Connector Adapter is the participant connection node for State / Company / Person.**
7. **G3 Escrow Foundation is not the same thing as GerChain's Escrow Engine.**
8. **NEF and GerChain are distinct infrastructures:** NEF establishes asset/wealth truth; GerChain governs value-flow conditions and movement.
9. **EXIM Port and DE–Country Port are distinct:** EXIM governs national CORE inbound/outbound flow; Country Port governs cross-border Digital Economy flow and sovereignty boundaries.
10. **Country-to-country interoperability must not bypass either country's CORE boundary.**
11. **TRINITY is cross-cutting and must not be introduced as G4 or as another architectural layer.**
12. **Adding a new country must not require redesigning G3, NEF, or GerChain.**
13. **Adding a new product must not require redesigning CORE.**
14. **SHUUD/SHIID are applications/products, not CORE engines.**
15. **The application layer consumes infrastructure services; it does not own infrastructure truth.**

## 5. G3 Escrow Principle

> **Үнэ цэнийг зөвхөн баталгаатай нөхцөл бүрдсэн үед хөдөлгөх боломжтой болгох.**
>
> Enable value to move only when the required conditions have been verified.

Canonical lifecycle:

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
→ RELEASE / DISPUTE
→ SETTLE / RESOLVE
→ RECONCILE
→ AUDIT
→ COMPLETE
```

## 6. International Flow Rule

The canonical cross-border flow is:

```text
COUNTRY A DE
→ DEE
→ G3 ESCROW FOUNDATION
→ NEF + GERCHAIN
→ EXIM PORT A
→ DE–A COUNTRY PORT
→ INTERNATIONAL DIGITAL ECONOMY FLOW
→ DE–B COUNTRY PORT
→ EXIM PORT B
→ I2B
→ MULTI-CONNECTOR ADAPTER
→ STATE / COMPANY / PERSON
```

Country Port must preserve jurisdiction, identity, authorization, regulatory boundaries, evidence, escrow conditions, settlement controls, and auditability.

## 7. Implementation Freeze Boundary

This document freezes the **architecture**, not the current implementation.

Implementation work may:
- rename modules to match the canonical architecture;
- move code across layers;
- remove forbidden direct dependencies;
- add tests and topology guards;
- reconcile existing PRs with this architecture;
- improve implementation without changing the canonical layer definitions.

Implementation work may not:
- introduce a new architectural layer without an explicit architecture change;
- create a second CORE or second authoritative Escrow/Witness engine;
- bypass EXIM Port for external CORE flow;
- connect applications directly to NEF/GerChain engines;
- redefine I2B as an Adapter;
- merge Country Port and EXIM Port into one concept;
- change NEF or GerChain's architectural role implicitly.

## 8. Governance

Any proposed change to this architecture must be made as an explicit architecture-change proposal and reviewed separately from ordinary feature development.

Until such a change is explicitly approved, this document is the canonical reference for architectural decisions in `butnee-sys/gerchain`.
