# EA-35 — FINAL EVIDENCE CONSOLIDATION / LOCK CANDIDATE

**Status:** VERIFIED / LOCK CANDIDATE — NOT YET LOCKED  
**Scope:** Fundamental GerChain value-flow infrastructure + EAI / Canonical Ledger / Canonical Escrow / Witness / Outbox / Durable Idempotency  
**Working branch:** feat/ea21-transaction-aware-ledger  
**Last reviewed:** 2026-09-28

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

An exact PostgreSQL execution SHA `890a78f36dcfe161e195da649b3cd124133d6535` has recorded successful production evidence:

- PostgreSQL production re-performance — run 36317914217 — SUCCESS
- Production PostgreSQL Runtime — run 36317914351 — SUCCESS
- production-postgres-smoke — run 36317914313 — SUCCESS
- production-postgres-proof — run 36317914446 — SUCCESS
- production-postgresql-gate — run 36317914344 — SUCCESS
- PostgreSQL production verification — run 36317914254 — SUCCESS
- EAI PostgreSQL Reperformance — run 36317914266 — SUCCESS
- EA-35 PostgreSQL re-performance — run 36317914249 — SUCCESS
- CodeQL Advanced — run 36317914278 — SUCCESS

These prove that real PostgreSQL execution has been achieved for the corresponding execution SHA.

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
