# EA-35 Production Lock Evidence

Status: PRODUCTION-READY EVIDENCE LOCKED
Scope: Fundamental architecture + EAI (Escrow as Infrastructure)
Excluded: product/application command layers

## Authoritative commit

- Branch: `feat/ea21-transaction-aware-ledger`
- Evidence SHA: `35feda34f7ebba2e4195219cce98456892ff9d73`

## Verified production gates

The exact evidence SHA reported successful GitHub Actions checks for:

- PostgreSQL smoke
- PostgreSQL production boot/runtime
- PostgreSQL production re-performance
- PostgreSQL E2E
- independent PostgreSQL evidence
- production-postgres evidence
- EAI production proof
- production smoke
- core reconciliation
- CodeQL / Python analysis

The migration runner was hardened to serialize publication with a PostgreSQL transaction-scoped advisory lock and the migration module was reduced to one authoritative implementation.

## Authority invariants

1. Canonical Ledger is the production value authority.
2. Canonical Escrow is the durable escrow truth.
3. Witness, Outbox and durable Idempotency remain evidence paths, not alternate value authorities.
4. FUND / RELEASE / REFUND / CANCEL / SETTLEMENT use the Canonical Ledger transaction boundary.
5. READ uses Canonical Ledger.
6. Production boot requires PostgreSQL.
7. Production schema is migration-authoritative; ORM `create_all()` is not the schema authority.
8. Legacy value stores are non-authoritative.
9. Recovery must not duplicate value movement.
10. Unknown/unverified conditions do not pass.

## Lock rule

No production implementation may introduce a second authoritative Ledger, Escrow, Witness Chain, or value-movement boundary without an explicit architecture-change proposal.

## Evidence qualification

A separate command-layer check remains outside this lock because product/application layers are explicitly excluded from the present EAI/fundamental-architecture production gate. Its failure is not used as evidence against this lock.

This document is evidence of the verified production gate, not an external certification or third-party attestation.
