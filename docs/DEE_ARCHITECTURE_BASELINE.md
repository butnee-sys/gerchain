# DEE Architecture Baseline v1

## Purpose

This document is the structural baseline for the NEF–GerChain Digital Escrow Ecosystem (DEE).
It defines the architecture before further identity, authorization, and security expansion.

## Canonical architecture

```text
                         DIGITAL ECONOMY
                                │
                               DEE
                                │
                        NEF + GERCHAIN
                       CORE INFRASTRUCTURE
                                │
                          CORE ADAPTER
                                │
                         ╔════════════╗
                         ║  EXIM PORT ║
                         ╚════════════╝
                                │
                       CONNECTOR ADAPTER
                                │
                    I2B MULTI-CONNECTOR GATEWAY
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
                 ТӨР         КОМПАНИ       ХУВЬ ХҮН
                  │             │             │
             Applications   Applications  Applications
                                │
                          SHUUD / SHIID
                            prototype
```

## Structural meaning

### 1. NEF + GerChain
The core digital-economic infrastructure.

- NEF: digital asset registration and valuation foundation.
- GerChain: escrow-based asset-flow infrastructure.
- Ledger, Money Engine, Escrow Engine, Witness Chain and Audit remain core services.

Business applications do not directly depend on these internals.

### 2. Core Adapter
The controlled adapter between the EXIM Port and NEF–GerChain internals.
It prevents the external architecture from depending on the internal package layout.

### 3. EXIM Port
The principal architectural boundary between the core infrastructure and the external economic world.
It coordinates and protects both inbound and outbound flows.

### 4. Connector Adapter
The controlled protocol/connector boundary immediately outside EXIM Port.
A connector adapter may translate an external connector protocol to the versioned EXIM Port contract.

### 5. I2B Multi-Connector Gateway
Infrastructure-to-Business multi-connector gateway.
It is extensible through controlled connector registration and dispatch.
It is not an application and is not limited to SHUUD.

### 6. Three external participant classes
The canonical external outputs are:

- **Төр** — government and public-sector systems.
- **Компани** — businesses and institutional commercial systems.
- **Хувь хүн** — individual users and participants.

These are participant classes, not implementation packages.

### 7. SHUUD / SHIID
SHUUD / SHIID is **one business application prototype** connected through the infrastructure.
It is not a core layer, gateway layer, or universal architectural dependency.

Replacing SHUUD / SHIID with another business application must not require redesigning NEF–GerChain, EXIM Port, or the I2B Gateway.

## Canonical flow

Inbound:

`Төр/Компани/Хувь хүн → Application → I2B Gateway → Connector Adapter → EXIM Port → Core Adapter → NEF–GerChain`

Outbound:

`NEF–GerChain → Core Adapter → EXIM Port → Connector Adapter → I2B Gateway → Application → Төр/Компани/Хувь хүн`

## Boundary rules

1. External applications never import NEF or GerChain internals directly.
2. External applications never bypass the I2B Gateway and Connector Adapter to reach EXIM Port.
3. Connector adapters are the controlled boundary for EXIM Port access.
4. Core access is isolated behind the Core Adapter.
5. SHUUD / SHIID is replaceable; it is not a required architectural layer.
6. New business applications can connect without changing the core infrastructure.
7. Security mechanisms are layered onto this structure; the structure itself is not treated as the complete security model.

## Structural acceptance criteria

The architecture baseline is accepted when tests can demonstrate:

- required architectural directories exist;
- the EXIM Port boundary exists;
- Connector Adapter exists between Gateway and Port;
- I2B Gateway exists independently of SHUUD;
- SHUUD is treated as an application prototype;
- the three participant classes are represented as external roles rather than core modules;
- prohibited direct imports remain blocked.
