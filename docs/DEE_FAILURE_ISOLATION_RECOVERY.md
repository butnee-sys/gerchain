# DEE Failure Isolation + Recovery

## Principle

A failed application, connector, gateway, escrow, or settlement operation must not automatically propagate into the protected NEF–GerChain core. Failure becomes an explicitly governed state.

## Canonical rule

`Failure → Isolate → Audit → Governed Recovery → Resume`

Recovery never bypasses the DEE Root of Trust.

## Isolation

- A component may be isolated without granting it recovery authority.
- Core isolation is a protective action, not a permission to mutate the core.
- Unknown recovery modes fail closed.
- Non-owner actors cannot authorize the recovery boundary.

## Recovery

Existing multi-party Recovery Governance remains the authority for emergency key/recovery decisions. Recovery requests are signed, threshold checked, role-diverse, replay protected, and hashed.

## Trinity

Isolation and recovery authorization require complete TRUST + TRANSPARENCY + PERFORMANCE proof. Missing proof is denial.

## Audit

Isolation and recovery decisions must be represented in the unified tamper-evident audit chain so the incident can be reconstructed without relying on mutable application state.
