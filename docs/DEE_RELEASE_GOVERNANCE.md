# DEE Release Governance

## Purpose

No adapter, connector, application, or release may reach protected NEF–GerChain execution by bypassing the DEE Root of Trust and Runtime Governance.

## Release gate

`Release Request → Owner Identity → Trinity → Signed Release Gate → Manifest Integrity → Protected Paths → Execution`

The existing signed-release gate remains authoritative for release signature, owner binding, commit binding, manifest integrity, protected paths, and release replay protection. DEE Release Governance adds the outer governance boundary and does not create a parallel release authority.

## Mandatory rules

1. Release actor must be bound to the DEE Owner.
2. Release request identity must match the signed release identity.
3. TRUST + TRANSPARENCY + PERFORMANCE must all be proven.
4. The existing `ReleaseAuthorization` gate must approve the signed release.
5. Failure is fail-closed.
6. Release decisions must be auditable through the unified DEE audit chain.
7. SHUUD/SHIID and other applications remain replaceable; release governance belongs to DEE, not to an application.

## Security boundary

`DEE Root of Trust → Runtime Governance → Release Governance → Protected Release Gate → NEF + GerChain`

A release mechanism is an execution gate, never an independent authority.
