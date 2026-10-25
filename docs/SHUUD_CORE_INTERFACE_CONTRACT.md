# SHUUD — GerChain CORE Interface Contract Boundary

## Purpose

Define the boundary between the SHUUD product and GerChain CORE without treating SHUUD business logic as CORE logic.

## SHUUD owns

- user interaction
- product workflow
- case lifecycle
- application decisions
- insurer-facing workflow
- road-operation workflow
- notifications
- product-specific evidence requirements

## CORE owns

- value-flow execution
- escrow state and conditions exposed through approved interfaces
- ledger integrity
- witness/evidence infrastructure
- idempotency guarantees
- transaction integrity
- recovery and reconciliation

## Contract principle

SHUUD may request an approved CORE capability through a defined interface. SHUUD must not directly manipulate CORE persistence structures or bypass CORE integrity controls.

## Change principle

A request for a new capability is not automatically a CORE change. It becomes a CORE change only after technical review establishes that the existing interface/capability is insufficient.

## Assurance principle

Interface tests are SHUUD evidence when they test SHUUD behavior. CORE evidence remains responsible for the underlying CORE guarantee. Both references should be linked by evidence identifiers.
