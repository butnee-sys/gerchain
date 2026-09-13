# DEE Connector Architecture v3

## Canonical topology

```text
DIGITAL ECONOMY
       │
      DEE
       │
  GOVERNANCE + TRUST + PROTECTION
       │
NEF–GERCHAIN
       │
Core Adapter
       │
EXIM Escrow Port
       │
Connector Adapter
       │
I2B Multi-Connector Gateway
       │
 ┌─────┼───────────────┐
 ▼     ▼               ▼
ТӨР  КОМПАНИ        ХУВЬ ХҮН
 │      │               │
Applications       Applications
        │
   SHUUD / SHIID
      prototype
```

The mandatory upper relationship is:

`Digital Economy → DEE → NEF + GerChain`

DEE is the protected governance and trust environment surrounding the NEF–GerChain core. It is not only an escrow mechanism and not only a runtime authorization component.

## DEE Genesis and protected trust

The DEE security/governance order is:

`DEE Genesis → Root of Trust → Runtime Governance → Authorization → Protection → Execution → Audit/Recovery`

Genesis establishes the trust anchor. The Root of Trust verifies protected changes against the authorized Owner public key. Runtime Governance then determines which identities may perform Architecture, Security Policy, Adapter Approval, and Release Approval actions.

The protected signing model is cryptographic and fail-closed:

- Owner identity is explicit.
- Owner public key is the verification anchor.
- Protected changes carry an attributable signature.
- Releases bind the Owner identity to the release identifier, commit SHA, manifest hash, and version.
- Private signing material is operational and must not be stored in the repository.

## Protected infrastructure path

`NEF–GerChain → Core Adapter → EXIM Port → Connector Adapter → I2B Multi-Connector Gateway`

This path operates under DEE governance. No external application or connector may bypass the governance and boundary controls to reach NEF–GerChain internals.

## External participant classes

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
9. Authorization, evidence, witness, release, settlement, audit, recovery, and connector lifecycle remain governed by DEE security and EXIM Port contracts.
10. No adapter, connector, application, or release may bypass the DEE Root of Trust and Runtime Governance.

## Security effect

DEE is the governing protection environment. The architecture creates distinct enforcement boundaries inside that environment:

- **Root of Trust:** cryptographic trust anchor for protected DEE changes and releases.
- **Runtime Governance:** Owner-controlled authority over architecture, security policy, adapter approval, and release approval.
- **Core Adapter:** protects NEF–GerChain internals.
- **EXIM Escrow Port:** protects the canonical economic contract surface.
- **Connector Adapter:** isolates each external protocol/connector from the Port implementation.
- **I2B Multi-Connector Gateway:** controls connector identity, registration, revocation, and dispatch.
- **Application Adapter:** isolates business-application logic from connector mechanics.

These boundaries are enforcement points of DEE governance; they are not substitutes for DEE governance itself.

## Extension rule

New systems are added as separate applications and, when necessary, separate application/connector adapters. They do not receive direct access to NEF–GerChain or EXIM Port internals.

Adding or replacing SHUUD / SHIID must not require redesigning NEF–GerChain, EXIM Port, I2B Gateway, or the DEE governance environment.
