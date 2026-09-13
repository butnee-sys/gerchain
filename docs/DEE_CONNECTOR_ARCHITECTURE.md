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
Open Multi-Connector Gateway
     │
     ▼
Application Adapter
     │
     ├── SHUUD
     ├── SHIID
     ├── Insurance
     ├── Bank
     ├── Government
     ├── Trade
     ├── Logistics
     └── RWA
```

The protected path is:

`EXIM PORT → Connector Adapter → Open Multi-Connector Gateway → Application Adapter → SHUUD/SHIID`

## Boundary rules

1. `nef_gerchain_port/` remains the versioned EXIM Escrow Port boundary.
2. `connectors/` is the only layer allowed to import `nef_gerchain_port` for external connector access.
3. `gateway/` contains no EXIM, NEF, GerChain, or application imports. It performs controlled connector registration and dispatch.
4. `application_adapters/` translates application-domain operations into gateway operations.
5. `shuud/` must not import `nef_gerchain_port`, NEF, GerChain engines, or their internal DTOs.
6. A connector is explicitly registered by connector ID; unknown or revoked connectors cannot be dispatched.
7. "Open" means extensible by controlled registration, not unauthenticated access.
8. Application-specific adapters are isolated, so a SHUUD failure does not create an implicit path to another connector.
9. Authorization, evidence, witness, release, settlement, and audit remain governed by the existing DEE security and EXIM Port contracts.

## Security effect

This architecture creates distinct trust boundaries:

- **Core Adapter:** protects NEF–GerChain internals.
- **EXIM Escrow Port:** protects the canonical economic contract surface.
- **Connector Adapter:** isolates each external protocol/connector from the Port implementation.
- **Open Multi-Connector Gateway:** controls connector identity, registration, revocation, and dispatch.
- **Application Adapter:** isolates SHUUD/SHIID domain logic from connector mechanics.

The additional layers are not security by themselves. Their security value comes from enforcing these dependency and authorization boundaries in code and tests.

## Extension rule

New systems are added as separate application adapters and, when necessary, separate connector adapters. They do not receive direct access to NEF–GerChain or the EXIM Port internals.
