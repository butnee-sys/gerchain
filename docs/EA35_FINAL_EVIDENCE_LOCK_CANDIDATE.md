# EA-35 — FINAL EVIDENCE CONSOLIDATION / LOCK CANDIDATE

**Status:** VERIFIED / LOCK CANDIDATE — NOT YET LOCKED  
**Scope:** Fundamental GerChain value-flow infrastructure + EAI / Canonical Ledger / Canonical Escrow / Witness / Outbox / Durable Idempotency  
**Working branch:** feat/ea21-transaction-aware-ledger  
**Last reviewed:** 2026-10-07

## 1. Purpose

This document consolidates the implementation, PostgreSQL execution, reconciliation, recovery, idempotency, authority, and security evidence produced during the current hardening cycle.

It is a closure document, not a new architecture layer.

## 2. Canonical authority

Production value authority is frozen to:

- `gerchain_ledger_accounts`
- `gerchain_ledger_movements`
- `PostgreSQLAtomicLedger.transfer_in_transaction()`
- `CanonicalLedgerRead`

Non-authoritative legacy value stores:

- `MoneyLedger`
- `ReleaseAccount`
- `AccountBalance`
- SQLite value stores
- application-owned balance mutation paths

Production paths must fail closed rather than silently falling back.

## 3. Canonical transaction graph

A committed value operation must reconcile as:

`ESCROW ↔ TRANSACTION_ID ↔ CANONICAL LEDGER MOVEMENT ↔ WITNESS ↔ OUTBOX ↔ IDEMPOTENCY`

For value movement, integrity is bound to:

`transaction_id + operation + escrow_id + source + destination + amount + currency`

LOCK is explicitly state-only and therefore does not require a Ledger movement.

## 4. Verified implementation areas

- FUND → Canonical Ledger
- LOCK → Canonical Escrow durable state
- RELEASE → Canonical Ledger
- REFUND → Canonical Ledger
- CANCEL → Canonical Ledger
- SETTLEMENT → Canonical Ledger
- BALANCE READ → Canonical Ledger
- durable Escrow READ
- durable idempotency
- transaction-aware Outbox
- transaction-aware Witness
- deep value-truth reconciliation
- movement/outbox operation binding
- replay/idempotency protection
- legacy mutation fail-closed boundaries
- production runtime construction correction

## 5. PostgreSQL evidence

### Current exact-SHA production verification

Current branch tip before this evidence-record commit: `52e2e1bce5952bbe7a91ac091dcf3c5eb5ba11e4`.

Fresh exact-SHA GitHub Actions evidence:

- `production-postgresql-gate` — run `37578103101` — SUCCESS
- `EAI PostgreSQL Production Proof` — run `37578103120` — SUCCESS
- `production-postgres` — run `37578103114` — SUCCESS
- `independent-postgresql-evidence` — run `37578103086` — SUCCESS
- `production-postgres-reperformance` — run `37578099616` — SUCCESS
- `EA-35 PostgreSQL production smoke` — run `37578099605` — SUCCESS
- `production-postgresql-e2e` — run `37578099474` — SUCCESS
- `postgres-production` — run `37578099673` — SUCCESS

The canonical production gate log records:
- PostgreSQL 16 live service
- production entrypoint initialized successfully
- Canonical Ledger authority established
- migration concurrency: `1 passed`
- deep value-truth reconciliation: `19 passed`
- EAI production re-performance: `1 passed`
- production PostgreSQL integration gate: `2 passed`

This is the first current-tip evidence set that covers the production-factory correction on the same execution SHA.

Historical successful evidence remains retained but is not used to substitute for current-tip proof.

## 6. Failed-run disposition

Failed workflows found on the same historical execution set are NOT silently discarded.

Observed categories:

### A. Environment/configuration mismatch
Examples:
- missing `GERCHAIN_DATABASE_URL`
- missing `GERCHAIN_TEST_DATABASE_URL`

Disposition: CI/test wiring issue, not evidence of a production value-authority failure. Must be corrected or explicitly retired before final CI closure.

### B. Stale/incompatible test assumptions
Examples:
- migration helper called while the SQLAlchemy connection is already in a transaction
- tests expecting obsolete transaction fixtures or account state
- legacy tests using interfaces no longer matching the canonical transaction-aware boundary

Disposition: test-suite reconciliation required.

### C. Genuine evidence mismatch
Examples:
- deep reconciliation detecting missing Outbox / durable Idempotency evidence in a test path
- E2E lookup failures
- canonical EAI integration expecting a different movement count

Disposition: cannot be waived. Each must be either fixed and re-run successfully, or explicitly proven to be outside the final canonical path.

## 7. Lock rule

The following are mandatory before declaring LOCKED:

1. One current immutable commit SHA containing the final implementation.
2. One canonical CI gate for the final SHA.
3. PostgreSQL production lifecycle success on that exact SHA.
4. Deep value-truth reconciliation success on that exact SHA.
5. No unexplained failed canonical production test.
6. Legacy value authority physically frozen/read-only or formally archived.
7. Final evidence index references exact run IDs and SHA.
8. Independent re-performance package retained.
9. Fundamental architecture freeze remains unchanged.
10. No second Ledger, Witness, Escrow Engine, or value authority introduced.

## 8. Current verdict

**Implementation:** substantially closed.

**Real PostgreSQL execution:** proven on retained execution SHA.

**Architecture:** frozen.

**Value authority:** frozen.

**EAI:** implemented and PostgreSQL re-performed.

**Final LOCK:** NOT YET DECLARED.

The remaining work is closure/reconciliation of evidence and final exact-SHA gate execution, not expansion of the architecture.


## 9. Exact-SHA re-verification trigger — 2026-09-30

This document is retained as a lock-candidate record. A fresh branch-tip CI execution must be attached to the exact commit containing this section before EA-35 is declared LOCKED. No prior successful SHA is treated as proof for a later SHA.
