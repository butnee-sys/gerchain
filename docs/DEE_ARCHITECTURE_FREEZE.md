# DEE Canonical Architecture Freeze v1

## Status

**CANONICAL / FROZEN**

This document locks the architectural relationships that define the NEF–GerChain Digital Escrow Ecosystem (DEE). It does **not** freeze implementation details, business applications, connectors, internal algorithms, or performance work.

## 1. Frozen architectural contract

The following relationships are mandatory:

```text
DIGITAL ECONOMY
      │
     DEE
      │
 NEF + GERCHAIN
      │
 CORE ADAPTER
      │
 EXIM PORT
      │
 CONNECTOR ADAPTER
      │
 I2B MULTI-CONNECTOR GATEWAY
      │
 ┌────┼────┐
 ▼    ▼    ▼
ТӨР  КОМПАНИ  ХУВЬ ХҮН
```

The upper-to-core relationship is permanently canonical:

**Digital Economy → DEE → NEF + GerChain**

## 2. DEE is the protected governance environment

DEE is not merely an escrow function and not merely a runtime module. DEE is the protected governance and trust environment surrounding the NEF–GerChain core infrastructure.

Its governing order is:

```text
DEE GENESIS
    ↓
ROOT OF TRUST
    ↓
GOVERNANCE
    ↓
AUTHORIZATION
    ↓
PROTECTION
    ↓
EXECUTION
    ↓
AUDIT / RECOVERY
```

No Adapter, Connector, Application, or Release may bypass the DEE Root of Trust or Governance.

## 3. Frozen boundaries

### Core boundary

`NEF + GerChain → Core Adapter → EXIM Port`

The external architecture must not depend directly on NEF or GerChain internal packages.

### External boundary

`EXIM Port → Connector Adapter → I2B Multi-Connector Gateway`

The gateway is the controlled multi-connector entry/exit point. Connector registration and dispatch remain subject to DEE governance.

### Participant boundary

The external participant classes are:

- **ТӨР**
- **КОМПАНИ**
- **ХУВЬ ХҮН**

These are participant classes, not infrastructure packages.

## 4. Application rule

SHUUD / SHIID is **one replaceable business application prototype**.

It is not a core layer, gateway layer, governance layer, or universal dependency.

The architecture must remain valid if SHUUD / SHIID is removed and replaced by another application.

## 5. Frozen security rule

The architectural boundaries are enforcement points inside DEE. They do not replace DEE governance.

The mandatory rule is:

> **DEE хамгаалалтыг гаднаас авдаггүй. DEE өөрөө хамгаалагдсан засаглалын орчин байна.**

Therefore:

1. DEE Root of Trust remains the authority anchor.
2. Owner governance remains authoritative for Architecture, Security Policy, Adapter Approval, and Release Approval.
3. Protected changes and releases must be attributable to the authorized Owner and verifiable against the Root of Trust.
4. Applications and connectors cannot establish a parallel authority path to NEF–GerChain.

## 6. What is frozen

The following are architectural invariants:

- Digital Economy → DEE → NEF + GerChain.
- DEE as the protected governance/trust environment.
- DEE Genesis → Root of Trust → Governance → Authorization → Protection → Execution → Audit/Recovery.
- NEF + GerChain as the core infrastructure.
- Core Adapter as the core boundary.
- EXIM Port as the principal architectural boundary.
- Connector Adapter between EXIM Port and I2B Gateway.
- I2B Multi-Connector Gateway as the controlled external connector boundary.
- ТӨР / КОМПАНИ / ХУВЬ ХҮН as external participant classes.
- SHUUD / SHIID as replaceable business application prototype.
- No direct application or connector bypass into the core.

## 7. What remains evolvable

The freeze does **not** prevent:

- new applications;
- new connectors;
- new participant integrations;
- internal implementation refactoring;
- new governance/protection controls that preserve the frozen authority model;
- performance optimization;
- database/runtime changes;
- API version evolution behind the frozen boundaries;
- new business products built on the infrastructure.

A proposed change that alters a frozen invariant is an **architecture change**, not a routine implementation change, and requires explicit Owner architectural approval before adoption.

## 8. Canonical principle

> **Architecture = түгжээтэй. Implementation = хөгжих боломжтой.**

The purpose of the freeze is to prevent architectural drift while allowing the NEF–GerChain infrastructure and its business ecosystem to continue evolving.
