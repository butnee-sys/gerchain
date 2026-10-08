# EA-35 PRODUCTION LOCK STATUS

Status: **TECHNICAL EVIDENCE VERIFIED / FORMAL LOCK WITHHELD**
Lock scope: **Overall/Fundamental Architecture + EAI (Escrow as Infrastructure)**
Repository: `butnee-sys/gerchain`
Branch: `feat/ea21-transaction-aware-ledger`

## Lock decision

The earlier LOCKED wording in this document is superseded by the current frozen verification governance and control matrix. Technical production evidence is verified, but final formal lock is withheld while organizational IAM/MFA assurance remains missing.

EA-35 production readiness is locked only after real PostgreSQL execution, canonical migration bootstrap, value-flow execution, deep value-truth reconciliation, EAI re-performance, independent PostgreSQL evidence, and repository security/operating gates all passed.

The authoritative production value boundary is the Canonical Ledger:
- `gerchain_ledger_accounts`
- `gerchain_ledger_movements`
- `PostgreSQLAtomicLedger.transfer_in_transaction()`

Production runtime authority is established only through:
- `ProductionRuntimeFactory`
- `ProductionRuntimeConfig`
- `initialize_canonical_postgres_schema()`
- canonical PostgreSQL migration runner
- `GerchainRuntime.configure_canonical_ledger()`

Legacy value authorities remain non-authoritative.

## Exact evidence

Latest executable evidence SHA:
`cd41c6ebd24783b7873405c59890358d03e7e653`

Latest documentation consolidation commit:
`a5dbe49880eea81012ec4c2783edc03681e1660f`

Successful exact-SHA production evidence for `cd41c6ebd24783b7873405c59890358d03e7e653`:
- production-postgresql-gate run **37720845287** — SUCCESS
- independent-postgresql-evidence run **37720845257** — SUCCESS
- EAI PostgreSQL Production Proof run **37720850002** — SUCCESS
- Production PostgreSQL Re-performance run **37720845329** — SUCCESS
- production-postgres run **37720845345** — SUCCESS
- production-postgresql-e2e run **37720845333** — SUCCESS
- EA-35 PostgreSQL production smoke run **37720845299** — SUCCESS


## Production gate results

The production PostgreSQL gate passed all required stages:
1. Python syntax gate
2. production factory and canonical persistence
3. production entrypoint boot against PostgreSQL
4. concurrent PostgreSQL migration bootstrap
5. deep value-truth reconciliation
6. EAI production re-performance
7. real PostgreSQL production value-flow gate

The value-flow gate covered:
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

## Critical correction closed before lock

A production PostgreSQL session-leak condition was identified in canonical balance reads. Each production `get_balance()` call previously retained a pooled session. This was corrected so every canonical balance read uses a short-lived session context.

Correction commit:
`983107aa79dfa182876a32604eeecf9066bb0323`

The correction was included in the subsequent exact-SHA evidence commit:
`12d154298944aa2c40a11d98cc4dfec17ccc1d94`

## Hard invariants locked

1. One authoritative Canonical Ledger.
2. No production balance mutation outside the Canonical Ledger boundary.
3. No second authoritative Escrow Engine.
4. No second authoritative Witness Chain.
5. No application-owned authoritative value truth.
6. Decision -> Authorization -> Release remains mandatory.
7. Trust + Transparency + Performance remain mandatory release conditions.
8. Unknown/unresolved required conditions fail closed.
9. Value movement and durable escrow transition occur within the same transaction boundary.
10. Replay cannot duplicate value movement.
11. Conflicting idempotency reuse is rejected.
12. Witness and Outbox evidence are bound to canonical movement semantics.
13. LOCK is state-only and does not require a value movement.
14. Recovery cannot create duplicate value movement.
15. Canonical migration publication is serialized and checksum-verified.
16. Production runtime cannot silently fall back to legacy value authority.

## Scope boundary

This lock covers the **overall/fundamental architecture + EAI** production foundation.

Product/application layers are outside this lock and must not mutate the protected production authority directly.

## Lock rule

Any future change to the locked architecture, authority boundary, migration semantics, transaction boundary, evidence model, or production runtime construction requires a new architecture-change proposal and a fresh production re-performance before the lock may be considered valid again.

Lock state: **FORMAL LOCK WITHHELD**

Technical evidence state: **VERIFIED**.

Required remaining closure: GC-IDM-001 and GC-IDM-002 organizational IAM/MFA evidence, plus organizational IAM/MFA evidence. The canonical production gate is already confirmed on the latest executable SHA; the documentation consolidation commit is documentation-only and is not substituted as executable evidence.
