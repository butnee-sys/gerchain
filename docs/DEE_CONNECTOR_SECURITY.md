# DEE Connector Security

## Purpose

Connector access is an extension point, not an authority boundary. Every connector must remain outside the protected NEF–GerChain core and enter through the governed DEE path.

## Mandatory path

`Application → I2B Multi-Connector Gateway → Connector Adapter → EXIM Port → Core Adapter → NEF + GerChain`

No connector may bypass EXIM Port or Core Adapter.

## Governance requirements

A protected connector request requires:

1. DEE Root of Trust
2. Owner-bound actor identity
3. Valid request and operation identity
4. Connector credential authentication
5. Nonce-based replay protection
6. Trinity: TRUST + TRANSPARENCY + PERFORMANCE
7. Core access authorization

Failure of any required condition is fail-closed.

## Gateway controls

The gateway stores only credential fingerprints, supports credential rotation and revocation, restricts operations by connector, and rejects reused request nonces. Audit records must never contain raw credential material.

## Authority rule

A connector, adapter, gateway, or application does not gain Owner authority merely because it is registered or can reach another layer. Authority originates in DEE Root of Trust and Runtime Governance.

## SHUUD rule

SHUUD/SHIID is a replaceable business application. It must use the same protected connector path and cannot become a security authority or architectural dependency of NEF–GerChain.
