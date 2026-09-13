# DEE Connector Architecture v2

## Canonical topology

```text
NEF–GerChain
     │
     ▼
Core Adapter
     │
     ▼
EXIM Escrow Port
     │
     ▼
Connector Adapter
     │
     ▼
I2B Multi-Connector Gateway
     │
     ├───────────────┬───────────────┐
     ▼               ▼               ▼
    ТӨР           КОМПАНИ         ХУВЬ ХҮН
     │               │               │
 Applications    Applications    Applications
                     │
                SHUUD / SHIID
                  prototype
```

The protected infrastructure path is:

`NEF–GerChain → Core Adapter → EXIM Port → Connector Adapter → I2B Multi-Connector Gateway`

The external participant classes are **Төр / Компани / Хувь хүн**. They are participant categories, not implementation packages.

SHUUD / SHIID is one replaceable business application prototype under the **Компани** participant class. It is not an architectural layer and is not required for the infrastructure to operate.

## Boundary rules

1. `nef_gerchain_port/` remains the versioned EXIM Escrow Port boundary.
2. `connectors/` is the only connector layer allowed to import `nef_gerchain_port` for external connector access.
3. `gateway/` contains no EXIM, NEF, GerChain, or application imports. It performs controlled connector registration and dispatch.
4. `application_adapters/` translates application-domain operations into gateway operations.
5. SHUUD / SHIID must not import `nef_gerchain_port`, NEF, GerChain engines, or internal DTOs.
6. A connector is explicitly registered by connector ID; unknown or revoked connectors cannot be dispatched.
7. "Open" means extensible by controlled registration, not unauthenticated access.
8. Application-specific adapters are isolated, so one business application failure does not create an implicit path to another connector.
9. Authorization, evidence, witness, release, settlement, and audit remain governed by the existing DEE security and EXIM Port contracts.

## Security effect

This architecture creates distinct trust boundaries:

- **Core Adapter:** protects NEF–GerChain internals.
- **EXIM Escrow Port:** protects the canonical economic contract surface.
- **Connector Adapter:** isolates each external protocol/connector from the Port implementation.
- **I2B Multi-Connector Gateway:** controls connector identity, registration, revocation, and dispatch.
- **Application Adapter:** isolates business-application logic from connector mechanics.

The layers are architectural boundaries, not security by themselves. Their security value comes from enforcing dependency and authorization rules in code and tests.

## Extension rule

New systems are added as separate applications and, when necessary, separate application/connector adapters. They do not receive direct access to NEF–GerChain or EXIM Port internals.

Adding or replacing SHUUD / SHIID must not require redesigning NEF–GerChain, EXIM Port, or the I2B Gateway.
