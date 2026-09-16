# Canonical Protection Architecture v1.0

**Status:** PROPOSED ARCHITECTURE CHANGE — pending explicit approval
**Base:** `docs/DEE_ARCHITECTURE_FREEZE.md`
**Scope:** Whole → Ecosystem → System → Subsystem protection model

## 1. Purpose

This document adds the protection-centered architectural model to the existing DE / DEE architecture. It does not silently replace the existing frozen architecture. Until an explicit architecture-change proposal is approved, `docs/DEE_ARCHITECTURE_FREEZE.md` remains the implementation source of truth.

## 2. Core hierarchy

```text
WHOLE
  ↓ protects
ECOSYSTEM
  ↓ protects
SYSTEM
  ↓ protects
SUBSYSTEM
```

The hierarchy is not merely a size or administrative hierarchy. It is a protection hierarchy.

## 3. Protection–Function Principle

> **Protection determines valid function.**

The valid function of a level is constrained by the protection boundary of the environment in which that function exists.

```text
Protected Environment
        ↓
Boundary
        ↓
Authorized Function
        ↓
Action / Flow
```

A function that crosses its valid protection boundary becomes unauthorized function expansion and must not acquire parent-level authority implicitly.

## 4. Protected-environment relationship

### Subsystem

The protected environment of a Subsystem is its parent System.

```text
Protected Environment(Subsystem) = System
```

### System

The protected ontological environment of a System is its Ecosystem.

```text
Protected Ontological Environment(System) = Ecosystem
```

### Ecosystem

The Whole is the protective layer of the Ecosystem.

```text
Protective Layer(Ecosystem) = Whole
```

Therefore:

```text
WHOLE
  ↓ protects
ECOSYSTEM
  ↓ protects ontological existence of
SYSTEM
  ↓ protects functional environment of
SUBSYSTEM
```

## 5. Protection is not control

Protection does not imply ownership, domination, or unrestricted control.

```text
Protection ≠ Control
Protection ≠ Ownership
Protection ≠ Domination
```

Protection means preservation of valid existence, boundary, authority, and flow at the relevant level.

## 6. System model

A System is defined as:

```text
System = Protected Function + Boundary + Space + Authority + Flow
```

Protection is not merely another feature. It establishes the conditions under which the System's function is valid.

## 7. Authority rule

```text
Authority ⊆ Boundary ⊆ Protection Environment
```

A Subsystem must not acquire authority beyond the boundary granted by its parent System. A System must not acquire authority that contradicts the ontological protection of its Ecosystem.

## 8. System self-decomposition

The protection model provides a mechanism for analyzing System Self-Decomposition:

```text
Subsystem
  ↓
Function Expansion
  ↓
Boundary Penetration
  ↓
Protection Failure
  ↓
Authority Distortion
  ↓
Polarization
  ↓
System Self-Decomposition
```

This is a proposed architectural hypothesis and audit model, not a claim that the sequence is an established universal scientific law.

## 9. Polarization tests

A subsystem or system is flagged for architectural polarization review if any of the following are true:

1. It can change parent-level rules without parent authorization.
2. It can acquire another subsystem's authority.
3. It can make its local truth authoritative for the parent system without an explicit contract.
4. It can recursively create parent-level authority inside itself.
5. It can bypass DEE, PORT, or Adapter protection boundaries.

## 10. Protection and resilience

Canonical resilience is defined as:

```text
Resilience = Protection Integrity
           + Boundary Integrity
           + Authority Integrity
           + Flow Regulation
```

These are architectural dimensions, not a numerical score.

## 11. Adapter principle

An Adapter is the boundary-preserving regulator between protected environments.

```text
Adapter = Boundary
         + Validation
         + Dose Regulation
         + Flow Control
```

The Adapter regulates, as applicable:

- identity
- authority
- quantity
- rate
- quality
- state
- context

and may produce:

```text
ALLOW / HOLD / REJECT
```

An Adapter must not become an unauthorized operational engine or acquire parent-level authority.

## 12. PORT principle

PORT remains the official architectural name.

The Mongolian conceptual explanation is:

> **PORT — үүдэл, үүсэл, боломж, холболтын архитектурын цэг.**

PORT represents the possibility/boundary for connection and expression. It is not a physical door and is not itself a new operational System.

## 13. PORT vs Adapter

```text
PORT
What can connect?
      ↓
ADAPTER
How may it cross?
      ↓
SYSTEM
What may it do?
      ↓
CORE
What is authoritatively executed?
```

## 14. Whole / Ecosystem / System / Subsystem matrix

| Level | Primary role | Protected object | Protective environment | Authority boundary | Flow boundary |
|---|---|---|---|---|---|
| WHOLE | Preserve conditions of the whole | Ecosystem existence | Higher ontological context | Protective layer | Ecosystem-level |
| ECOSYSTEM | Preserve common ontological space | System existence, boundaries, coexistence | WHOLE | System-level boundaries | System ↔ System |
| SYSTEM | Execute bounded purpose | Subsystem functional environment | ECOSYSTEM | Subsystem authority | System ↔ Subsystem |
| SUBSYSTEM | Execute specialized function | Local state/function | SYSTEM | Granted local authority | Controlled input/output |

## 15. Operational component matrix

| Component | Canonical function | Protection concern | Authority rule |
|---|---|---|---|
| NEF | Asset registration, valuation, verification truth | Asset truth integrity | Own asset truth; do not become operational value-flow authority |
| GerChain | Asset value-flow infrastructure | Value-flow and state integrity | Own operational value-flow truth |
| Escrow Engine | Operational escrow state/transition | Conditional value protection | No direct release outside governed path |
| Witness | Evidence / event proof | Evidence integrity | Evidence is not execution authority |
| Audit | Verification / traceability | Audit integrity | Audit is not execution authority |
| Adapter | Boundary regulation | Boundary and authority integrity | Translation/regulation only |
| PORT | External connection possibility | External boundary integrity | Connection point, not operational authority |
| CORE | Authoritative execution | Canonical state integrity | Final authorized state transition |

## 16. Truth separation

The architecture must preserve distinct truth domains:

```text
NEF       = Asset Truth
Witness   = Evidence Truth
GerChain  = Asset Value-Flow Truth
CORE      = Execution / State Truth
```

No subsystem may silently absorb another subsystem's authoritative truth domain.

## 17. HOLD and fail-closed

HOLD is a protection state, not necessarily an error.

```text
VALID      → EXECUTE
UNCERTAIN  → HOLD
INVALID    → REJECT
```

For required unresolved conditions:

```text
UNKNOWN ≠ PASS
UNKNOWN → HOLD / REJECT
```

## 18. Canonical flow protection

External and cross-system flows must pass through the appropriate boundary:

```text
External
  ↓
PORT
  ↓
ADAPTER
  ↓
SYSTEM
  ↓
CORE
```

A direct external-to-core mutation is a protection-boundary violation unless explicitly defined by the canonical architecture and protected by an equivalent authoritative boundary.

## 19. GREEN / LOCK rule

A system is not GREEN merely because functional tests pass.

Canonical GREEN requires evidence of:

```text
Function Integrity
+ Protection Integrity
+ Boundary Integrity
+ Authority Integrity
+ State Integrity
+ Evidence Integrity
+ Runtime Integrity
```

Then:

```text
GREEN → LOCK
```

only after the required evidence is complete.

## 20. Implementation audit questions

For every GerChain component, the audit must answer:

1. What is its function?
2. What environment protects it?
3. What does it protect?
4. Where is its boundary?
5. Who owns its authority?
6. What flow may cross the boundary?
7. What evidence proves the operation?
8. What happens when conditions are unknown?
9. How does recovery preserve one-time execution?
10. Can any legacy path bypass the canonical boundary?

## 21. Required next implementation stage

Before SHUUD is advanced, the current GerChain implementation must be mapped against this matrix.

Classify every relevant path as:

```text
GREEN   = conforms to canonical boundary
YELLOW  = refactor required
RED     = bypass / duplicate authority / conflicting truth
```

The resulting gap audit must cover, at minimum:

- production runtime bootstrap
- authoritative CORE endpoint
- PostgreSQL persistence and transaction ownership
- release authority
- outbox processing and recovery
- legacy API paths
- legacy persistence paths
- network/CLI entry points
- EXIM boundary
- NEF ↔ GerChain boundary
- G-3 / EG3 boundary
- application boundary

## 22. Architecture governance

This document proposes an extension to the frozen architecture. It must be explicitly approved before being treated as the new canonical implementation source of truth.

Until approval:

```text
DEE_ARCHITECTURE_FREEZE.md = current implementation authority
CANONICAL_PROTECTION_ARCHITECTURE_V1.md = proposed extension
```
