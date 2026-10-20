# MASTER PRODUCTION WORK PLAN — Step 3 Reconciliation

**Status:** IMPLEMENTATION HARDENED / VALIDATION OPEN — NOT LOCKED  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Scope:** Step 3 — Reconciliation only. This record does not declare the full production architecture or EAI production-ready.

## Purpose

Step 3 reconciles the authoritative Canonical Ledger movement graph with durable Escrow, Witness, Outbox and Idempotency evidence, and checks the old balance stores against the canonical balance store without mutating any store.

## Invariants

1. Reconciliation is read-only.
2. Canonical Ledger movements are the sole authoritative value-movement records.
3. A value-moving operation must bind to the expected escrow (except SETTLEMENT, whose aggregate key is its transaction ID), matching witness, matching outbox event, completed durable idempotency record, and integrity hash.
4. CREATE, LOCK, and CREATED-state CANCEL are state-only operations. They must have zero value movement and a complete aggregate/witness/outbox/idempotency evidence graph.
5. A state-only event must never be treated as a value movement, and missing state-only evidence must not be silently accepted.
6. Same transaction ID with contradictory event type, aggregate, or evidence is a reconciliation issue.
7. Balance equality alone is insufficient: movement/evidence graph equality is also required.
8. Reconciliation never repairs or rewrites evidence; it reports mismatches for controlled remediation.

## Implementation hardening

File: `persistence/deep_value_reconciliation.py`

- Added explicit completeness checks for state-only CREATE, LOCK, and no-movement CANCEL witness records.
- Added outbox-side checks to detect state-only outbox events without the matching aggregate, zero-amount witness, and completed idempotency record.
- Added strict zero-movement payload validation for state-only CANCEL.
- Existing value-movement checks remain: operation, escrow reference, witness type/aggregate/amount, outbox type/aggregate, completed idempotency, positive amount, and SHA-256 integrity binding.
- Existing balance-store reconciliation remains read-only and compares account-set/balance differences across Canonical Ledger, ReleaseAccount, and AccountBalance.

## Added regression tests

File: `tests/persistence/test_deep_value_reconciliation.py`

- Detects state-only LOCK missing both outbox and completed idempotency evidence.
- Accepts complete state-only LOCK evidence with zero Ledger movements.

## Change commits

- Reconciliation implementation: `52ce7a67b86430983fdebbaf6f01b7d64d319390`
- Regression tests: `4a90c3cdf47b2d2692bdbffa80497fa7314739c2`

## Verification status

The implementation and regression-test changes are committed to the feature branch. A workflow-run lookup for test commit `4a90c3cdf47b2d2692bdbffa80497fa7314739c2` returned no PR-associated workflow runs. Therefore the tests have **not yet been independently verified as executed on this exact SHA**.

Required to close Step 3:
1. Run the focused deep reconciliation test file.
2. Run the full required test/CI gates against the exact final commit SHA.
3. Run the PostgreSQL reconciliation proof against the migrated schema and retain its artifact.
4. Verify the report is matched for clean data and produces the expected issue codes for each negative case.
5. Review the resulting evidence independently and record the exact SHA/run/artifact.

Until all five items are evidenced, Step 3 remains **IMPLEMENTATION HARDENED / VALIDATION OPEN**. It must be included as a mandatory control in FINAL LOCK, not represented as already closed.

## FINAL LOCK inclusion

FINAL LOCK must explicitly include:

- [ ] Step 3 — balance-store reconciliation: no unexplained account/currency/balance mismatch.
- [ ] Step 3 — deep value-truth reconciliation: no unexplained movement/escrow/witness/outbox/idempotency/integrity mismatch.
- [ ] State-only CREATE / LOCK / CANCEL evidence checks pass without false positives.
- [ ] Focused tests and full CI pass on the exact audited SHA.
- [ ] PostgreSQL re-performance artifact is retained and tied to the same SHA.
- [ ] Independent review signs off on the reconciliation evidence.

No reconciliation finding may be suppressed merely to obtain a matched report. Any mismatch leaves the gate OPEN/HOLD.
