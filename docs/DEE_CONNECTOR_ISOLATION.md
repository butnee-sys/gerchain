# DEE Cross-Connector Isolation

## Principle

Each connector operates in its own security context. A connector must never obtain another connector's credential context, nonce namespace, authorization context, state, or audit authority.

## Mandatory rule

`CONNECTOR-A → CONNECTOR-A` is permitted only through the governed DEE path. `CONNECTOR-A → CONNECTOR-B` is denied by default.

## Protected dimensions

- connector identity
- request identity
- nonce/replay namespace
- credential context
- authorization context
- connector state
- audit context

Cross-connector access is not an application feature and cannot be enabled merely by gateway registration.

## Governance

Isolation remains subordinate to DEE Root of Trust, Runtime Governance, Connector Governance, and the cross-cutting Trinity: TRUST + TRANSPARENCY + PERFORMANCE.

## Failure mode

Any ambiguous, missing, mismatched, or incomplete isolation condition must fail closed.
