# DEE Architecture Baseline v1

## Purpose

This document is the structural and governance baseline for the NEF–GerChain Digital Escrow Ecosystem (DEE).
It defines the architecture and the protected governance environment before further identity, authorization, connector, and security expansion.

## Foundational principle

**DEE is not merely an escrow feature and not merely a runtime governance module. DEE is the protected governance and trust environment in which the NEF–GerChain digital-economic infrastructure is authorized, changed, connected, executed, audited, and recovered.**

The canonical trust order is:

`DEE Genesis → Root of Trust → Runtime Governance → Authorization → Protection → Execution → Audit/Recovery`

The DEE Protection stage is governed by the cross-cutting **Trinity** principle:

`TRUST + TRANSPARENCY + PERFORMANCE`

Trinity is not an application layer and is not limited to escrow. It is the three-dimensional protection criterion applied across authorization, evidence, execution, settlement, connectors, and audit. Escrow Trinity tests are one concrete enforcement of this broader DEE protection principle.

Owner authority is cryptographically anchored. Protected changes and releases must be attributable to the authorized Owner and verifiable against the DEE Root of Trust. Private signing material is operationally external to the repository; the runtime verifies signatures against the Owner public key.

## Canonical architecture

```text
                         DIGITAL ECONOMY
                                │
                               DEE
                GOVERNANCE + TRUST + PROTECTION
                                │
             ┌──────────────────┴──────────────────┐
             │                                     │
        DEE GENESIS                         PROTECTED RUNTIME
             │                                     │
       ROOT OF TRUST                                │
             │                                     │
     RUNTIME GOVERNANCE                              │
             │                                     │
        OWNER AUTHORITY                              │
             │                                     │
             └──────────────────┬──────────────────┘
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

**Digital Economy → DEE → NEF + GerChain** is the mandatory upper-to-core relationship.
DEE is the Digital Escrow Ecosystem that provides the protected governance, trust, and coordination environment around the NEF–GerChain core infrastructure.
NEF + GerChain is therefore not presented as a standalone lower-level system; it is explicitly positioned within the DEE under the Digital Economy.

## DEE Genesis and governance structure

### 0. Root of Trust

DEE Genesis establishes the initial trust anchor for protected DEE operation.

- **Owner Identity** identifies the authoritative owner.
- **Owner Public Key** is the cryptographic verification anchor.
- **Genesis Anchor** binds the initial DEE security state.
- **Policy Version** identifies the governing security policy state.
- Protected changes and releases are cryptographically signed and verified against the Root of Trust.

### 1. Runtime Governance

The Owner is the highest runtime governance authority for protected DEE changes.

```text
OWNER
 ├─ Architecture
 ├─ Security Policy
 ├─ Adapter Approval
 └─ Release Approval
```

Runtime governance is deny-by-default. Operator and application roles do not inherit Owner powers.

### 2. DEE protection domains

The DEE governance environment governs, at minimum:

- Identity and authorization
- Security policy
- Contract governance
- Evidence governance
- Escrow state and release governance
- Witness and verification
- Audit and traceability
- Key and recovery governance
- Connector registration and lifecycle
- Failure isolation

These are governance/protection domains of DEE, not separate external architectural layers.

### 3. Trinity protection principle

Trinity is the cross-cutting protection rule for the domains above:

```text
                    DEE PROTECTION
                         │
              ┌──────────┼──────────┐
              │          │          │
            TRUST   TRANSPARENCY PERFORMANCE
              │          │          │
              ▼          ▼          ▼
        identity /    evidence /   contract /
        authorization witness /    escrow /
        signing       verification money /
        governance    audit         settlement
```

A protected operation is allowed only when all three dimensions are satisfied. Missing or failed proof in any dimension is fail-closed.

## Structural meaning

### 0. Digital Economy → DEE → NEF + GerChain

- **Digital Economy** — the broader economic environment and purpose.
- **DEE** — Digital Escrow Ecosystem; the protected governance, trust, and coordination environment between the Digital Economy and the NEF–GerChain core.
- **NEF + GerChain** — the core digital-economic infrastructure operating within DEE.

This relationship is mandatory in every canonical architecture representation.

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
It coordinates and protects both inbound and outbound flows under DEE governance.

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

All protected changes, connector approvals, releases, and security-sensitive operations remain subject to DEE governance and Root-of-Trust verification.

## Boundary rules

1. External applications never import NEF or GerChain internals directly.
2. External applications never bypass the I2B Gateway and Connector Adapter to reach EXIM Port.
3. Connector adapters are the controlled boundary for EXIM Port access.
4. Core access is isolated behind the Core Adapter.
5. SHUUD / SHIID is replaceable; it is not a required architectural layer.
6. New business applications can connect without changing the core infrastructure.
7. **DEE governance is the security environment; the architectural boundaries are enforcement points within that environment.**
8. No adapter, connector, application, or release may bypass the DEE Root of Trust and Runtime Governance.
9. **Digital Economy → DEE → NEF + GerChain** must remain present in canonical architecture documentation and structural tests.
10. **Trinity is a cross-cutting DEE protection principle, not a separate application or architecture layer.**
11. A protected operation must satisfy **TRUST + TRANSPARENCY + PERFORMANCE**; missing proof fails closed.

## Structural acceptance criteria

The architecture baseline is accepted when tests can demonstrate:

- required architectural directories exist;
- the **Digital Economy → DEE → NEF + GerChain** relationship is explicitly documented;
- DEE Genesis / Root of Trust / Runtime Governance are explicitly documented;
- Owner governance covers Architecture, Security Policy, Adapter Approval, and Release Approval;
- the EXIM Port boundary exists;
- Connector Adapter exists between Gateway and Port;
- I2B Gateway exists independently of SHUUD;
- SHUUD is treated as an application prototype;
- the three participant classes are represented as external roles rather than core modules;
- prohibited direct imports remain blocked;
- Trinity is explicitly defined as the cross-cutting DEE protection principle;
- Trinity protection is fail-closed when any dimension is missing or invalid.
