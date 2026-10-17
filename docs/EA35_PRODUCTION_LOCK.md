# EA-35 Production Lock Evidence

Status: **TECHNICAL PRODUCTION EVIDENCE VERIFIED / FORMAL LOCK WITHHELD**
Scope: **Fundamental architecture + EAI (Escrow as Infrastructure)**
Excluded: product/application command layers

## Exact tested code state

- Branch: `feat/ea21-transaction-aware-ledger`
- Exact tested code SHA: `19061aa63bec90e35d82d8392e372cc113b3ead4`
- Current documentation commit: `fc8b1f22826d5b037bf7bf8123ad2c77b1221583`
- Documentation-only commits do not change the tested production code state.

## Verified production gates on exact tested code SHA

- EAI PostgreSQL Production Proof — run **37715147549** — SUCCESS
- production-postgres — run **37715147558** — SUCCESS
- independent-postgresql-evidence — run **37715147637** — SUCCESS
- production-postgresql-reperformance — run **37715147584** — SUCCESS
- Production PostgreSQL Re-performance — run **37715147593** — SUCCESS
- production-postgresql-gate — run **37715147524** — SUCCESS
- core-gates — run **37715147544** — SUCCESS
- CORE Operating Reconciliation — run **37715147609** — SUCCESS
- CodeQL Advanced — run **37715147634** — SUCCESS

## Direct PostgreSQL evidence

The authoritative production gate verified:

1. Python syntax.
2. Production factory and canonical persistence.
3. Production entrypoint boot against real PostgreSQL.
4. Concurrent PostgreSQL migration bootstrap.
5. Deep value-truth reconciliation.
6. EAI production re-performance.
7. Real PostgreSQL value-flow.

The verified value-flow includes:

- FUND
- LOCK
- RELEASE
- REFUND
- CANCEL
- SETTLEMENT
- canonical balance reads
- replay/idempotency
- witness evidence
- outbox evidence
- deep reconciliation

Direct evidence includes:
- production boot: **1 passed**
- production factory gate: **2 passed**
- deep value reconciliation: **19 passed**
- independent persisted-value verification: **1 passed**
- migration serialization gate: **1 passed**
- EAI production re-performance: **1 passed**

## Authority invariants

1. Canonical Ledger is the production value authority.
2. Canonical Escrow is the durable escrow truth.
3. Witness, Outbox and durable Idempotency are evidence paths, not alternate value authorities.
4. FUND / RELEASE / REFUND / CANCEL / SETTLEMENT use the Canonical Ledger transaction boundary.
5. READ uses Canonical Ledger.
6. Production boot requires PostgreSQL.
7. Production schema is migration-authoritative.
8. Legacy value stores are non-authoritative.
9. Recovery cannot duplicate value movement.
10. Unknown/unverified conditions do not pass.

## Formal lock exclusion

Formal production lock is **not** declared by this document.

Remaining organizational closure includes:
- **GC-IDM-001** Identity / privileged access governance evidence.
- **GC-IDM-002** MFA / privileged account assurance evidence.

These are organizational assurance controls and cannot be fabricated from repository test results.

## Lock rule

Any future change to the locked architecture, authority boundary, migration semantics, transaction boundary, evidence model, or production runtime construction requires an architecture-change proposal and fresh production re-performance.

**Technical evidence: VERIFIED.**

**EAI + fundamental architecture: PRODUCTION-READY TECHNICAL EVIDENCE.**

**Formal production lock: WITHHELD pending organizational IAM/MFA evidence.**

This document is evidence of repository verification, not external certification or third-party attestation.
