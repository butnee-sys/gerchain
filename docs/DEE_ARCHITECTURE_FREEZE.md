# DEE Architecture Freeze

**Status:** FROZEN — Conceptual Architecture
**Freeze date:** 2026-09-14
**Repository:** `butnee-sys/gerchain`

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
STATE / COMPANY / PERSON
↓
ADAPTER
↓
DIGITAL ECONOMY ACTIONS
```

## Hard Architectural Rules

1. No direct external access to CORE.
2. CORE external inbound/outbound flow is governed through EXIM Port.
3. No application may directly depend on NEF or GerChain engines.
4. All real external system connections are implemented through Adapters.
5. I2B Gateway is a routing/selection layer, not the connector itself.
6. Multi-Connector Adapter is the participant connection node for State / Company / Person.
7. G3 Escrow Foundation is not the same thing as GerChain's Escrow Engine.
8. NEF and GerChain are distinct infrastructures: NEF establishes asset/wealth truth; GerChain governs value-flow conditions and movement.
9. EXIM Port and DE–Country Port are distinct: EXIM governs national CORE inbound/outbound flow; Country Port governs cross-border Digital Economy flow and sovereignty boundaries.
10. Country-to-country interoperability must not bypass either country's CORE boundary.
11. TRINITY = TRUST + TRANSPARENCY + PERFORMANCE is cross-cutting, not a separate layer or engine.
12. Adding a new country must not require redesigning G3, NEF, or GerChain.
13. Adding a new product must not require redesigning CORE.
14. SHUUD/SHIID are applications/products, not CORE engines.
15. The application layer consumes infrastructure services; it does not own infrastructure truth.

## G3 Escrow Principle

> Үнэ цэнийг зөвхөн баталгаатай нөхцөл бүрдсэн үед хөдөлгөх боломжтой болгох.

Canonical lifecycle:

```text
CREATE → IDENTIFY → AUTHORIZE → DEFINE CONDITIONS → FUND → LOCK
→ EXECUTE → COLLECT EVIDENCE → WITNESS → VERIFY → DECIDE
→ RELEASE / DISPUTE → SETTLE / RESOLVE → RECONCILE → AUDIT → COMPLETE
```

## International Flow Rule

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

## Implementation Freeze Boundary

This document freezes the **architecture**, not the current implementation.

Implementation may refactor modules, dependencies, tests, and topology to conform to this document. It may not silently redefine layers, create a second CORE, bypass EXIM Port for external CORE flow, connect applications directly to core engines, or redefine I2B as an Adapter.

Any architectural change requires an explicit architecture-change proposal and separate approval.
