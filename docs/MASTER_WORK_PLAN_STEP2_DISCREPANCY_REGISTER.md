# MASTER WORK PLAN — STEP 2 DISCREPANCY REGISTER

Date opened: 2026-10-19
Repository: `butnee-sys/gerchain`
Branch: `feat/ea21-transaction-aware-ledger`
Baseline: `docs/MASTER_WORK_PLAN_STEP1_FINAL_LOCK.md`
Status: **IN PROGRESS / NOT LOCKED**

## Progress measure

- Audit targets in initial register: 10
- Targets with source-level evidence inspected in this pass: 4
- Targets with at least one confirmed discrepancy or residual-risk surface: 3
- Targets fully closed with code + tests + migration/dependency evidence: 0
- Step 2 completion: **0% closed**; initial reconnaissance coverage **40% (4/10 targets inspected)**.

Coverage is not the same as closure. No deletion, migration, or architecture change is authorized by this register alone.

## Confirmed findings / residual-risk surfaces

### S2-01 — Legacy balance authority models remain in repository
**Status: CONFIRMED RESIDUAL SURFACE / OPEN**

Evidence:
- `persistence/atomic_release.py` blob SHA: `7de1ca3f9d827f96c39281231ab53d127b030f16`
  - Declares `ReleaseAccount` on `gerchain_release_accounts`.
- `persistence/atomic_settlement.py` blob SHA: `3e631b140e6c8ac8c2d4263ef09e4118d4af291f`
  - Declares `AccountBalance` on `gerchain_account_balances`.
  - Declares `SettlementMovement` on `gerchain_settlement_movements`.
- Canonical target remains `gerchain_ledger_accounts` and `gerchain_ledger_movements`.

Risk: duplicate balance/movement models remain available to be accidentally reintroduced as authorities. Their mere existence is not proof they are reachable from the production path; reference and dependency analysis remains required.

Required action: classify all imports/callers, prove non-reachability from production runtime, then propose freeze/archive/removal only after migration/reconciliation evidence.

### S2-02 — Legacy escrow truth model remains in repository
**Status: CONFIRMED RESIDUAL SURFACE / OPEN**

Evidence:
- `persistence/atomic_release.py` blob SHA: `7de1ca3f9d827f96c39281231ab53d127b030f16`
  - Declares `ReleaseEscrow` on `gerchain_release_escrows`.
- Canonical aggregate is implemented separately in `persistence/escrow_aggregate.py`.

Risk: two escrow-state representations may be confused or read by legacy code. Reachability, migrations, and existing-data ownership must be established before removal.

### S2-03 — Outbox has a durable model and more than one access interface
**Status: MODEL SHARED; DUPLICATE AUTHORITY NOT PROVEN / OPEN**

Evidence:
- `persistence/recovery_outbox.py` blob SHA: `51abd32213c3f9b572d40d38007d57b9c065c246` declares `OutboxEvent` on `gerchain_outbox_events` and `PostgreSQLOutbox`.
- `persistence/transactional_outbox.py` blob SHA: `5ed6b1d6cb6d27324f647b54eb4af38177eeb124` imports that same `OutboxEvent` and provides caller-transaction `enqueue_in_transaction`.

Assessment: two interfaces do not automatically mean two authorities; the transactional writer correctly avoids opening/committing its own session. The next audit must identify all producers and ensure production business writes use the transaction-participating function, while the lease worker only delivers committed events.

### S2-04 — Runtime has a test-memory construction path alongside canonical production configuration
**Status: INTENTIONAL SEPARATION; FAIL-CLOSED BEHAVIOR MUST BE PROVEN / OPEN**

Evidence:
- `services/gerchain_runtime.py` blob SHA: `46fa0a4e5a4d92a0b687270339cd83fdbb357bdd` imports `MoneyLedger`, `MoneyEngine`, and `AuthoritativeEscrowService`; its class documentation says default construction is a test-memory harness and production must explicitly attach Canonical Ledger.
- `services/gerchain_runtime_factory.py` blob SHA: `b130c64f17d114efaef28d80173c026c98bd84c7` owns production configuration and canonical schema initialization.

Assessment: the test-memory path is not itself a defect if production operations fail closed without canonical authority. Need line-by-line review of every value-moving method and all entrypoints to prove no production fallback remains.

## Open targets not yet verified in this pass

- S2-05 durable vs in-memory idempotency call-site reachability.
- S2-06 runtime-mode / authority-flag conflation.
- S2-07 versioned migration registry vs metadata `create_all`, including supported prior-schema upgrade.
- S2-08 all direct SQL mutation routes, CLI/UI/workers/scripts.
- S2-09 CREATE durability and schema/model lifecycle parity.
- S2-10 operation/event identifier and movement↔escrow↔witness↔outbox↔idempotency reconciliation.

## Step 2 work order

1. Inspect production factory initialization and schema guard in full.
2. Inspect all runtime methods: CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, READ.
3. Trace every import/call-site for legacy balance and escrow models.
4. Verify one authoritative outbox table and producer/consumer paths.
5. Verify durable idempotency fingerprints and state-only operation handling.
6. Inspect migration registry and test clean install + repeat run + supported prior-schema upgrade.
7. Turn each confirmed discrepancy into a minimal fix with regression tests.
8. Re-run deep value-truth reconciliation and exact-SHA CI before closing any item.

**Step 2 status: IN PROGRESS / NOT LOCKED.**
**Production readiness: NOT DECLARED.**
