# DEE I2B Gateway Security

## Principle

The I2B Multi-Connector Gateway is a controlled entry point, not an authority. Its ability to dispatch a connector operation never grants Owner authority and never bypasses DEE governance.

## Mandatory authorization chain

`DEE Root of Trust → Runtime Governance → Gateway Governance → Connector Governance → EXIM Port`

The gateway must fail closed when identity, operation, nonce, credential, or Trinity proof is missing or invalid.

## Boundary

The gateway must not import NEF or GerChain internals. It may route to registered connector adapters only. Connector adapters remain subject to the DEE Connector Governance gate.

## Trinity

Every protected gateway operation carries the cross-cutting Trinity proof:

- TRUST
- TRANSPARENCY
- PERFORMANCE

The gateway cannot replace or manufacture these proofs. It can only pass a request onward after the governance gate accepts them.

## Replaceability

Applications such as SHUUD/SHIID are clients of the infrastructure. Removing or replacing an application must not change the Gateway's authority model or the protected NEF–GerChain core.
