# FINAL LOCK CANDIDATE — PRODUCTION EVIDENCE

Status: FINAL LOCK CANDIDATE / PENDING FORMAL LOCK

Evidence commit under review:
- Branch: `feat/ea21-transaction-aware-ledger`
- Branch tip: `c62414218d8b44b2aef252c40342ddc9c7e75141`

## Production evidence

GitHub Actions workflow runs associated with the branch tip:

| Gate | Run | Result |
|---|---:|---|
| production-postgresql | 37638752353 | PASS |
| production-postgresql-reperformance | 37638752556 | PASS |
| production-postgresql-gate | 37638752547 | PASS |
| independent-postgresql-evidence | 37638752430 | PASS |
| EAI PostgreSQL Production Proof | 37638752338 | PASS |
| core-gates | 37638752330 | PASS |
| CORE Operating Reconciliation | 37638752500 | PASS |
| CodeQL Advanced | 37638752391 | PASS |

## Verified production gates

The successful production gate explicitly verified:

1. Exact evidence commit recording.
2. Python syntax gate.
3. Production factory and canonical persistence.
4. PostgreSQL production entrypoint boot.
5. Concurrent migration bootstrap serialization.
6. Deep value-truth reconciliation.
7. EAI production re-performance.
8. Real PostgreSQL production value-flow gate.

Additional production workflow verification:
- Canonical production tables: PASS.
- Canonical Ledger movement: PASS.
- Canonical Ledger replay/idempotency: PASS.
- Deep reconciliation regression: PASS.
- Deep reconciliation suite: 19 passed.
- PostgreSQL migration concurrency test: 1 passed.
- EAI production re-performance: 2 passed.
- Independent PostgreSQL persisted-value evidence: 1 passed.
- EAI production runtime: 2 passed.

## Authority assertions

Production runtime is required to:
- use PostgreSQL;
- apply numbered migrations;
- reject incomplete canonical production schema;
- configure the Canonical Ledger boundary;
- fail if Canonical Ledger authority is not established.

Production value authority remains:
- `gerchain_ledger_accounts`
- `gerchain_ledger_movements`
- `PostgreSQLAtomicLedger` transaction-aware boundary.

Legacy value stores remain non-authoritative.

## Deep value-truth invariant

For committed value movement, reconciliation requires alignment across:
- canonical Ledger movement;
- durable Escrow aggregate;
- Witness evidence;
- Outbox evidence;
- durable Idempotency evidence;
- movement integrity hash.

State-only LOCK operations are explicitly separated from value-movement reconciliation.

## Important historical failure and closure

An earlier run on commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` failed because of:
- a runtime syntax corruption;
- PostgreSQL migration publication race;
- an escrow state constraint mismatch in the earlier test path.

These failures are not treated as green evidence. Subsequent commits corrected the runtime and migration publication path, and the current branch tip has fresh successful production gates.

## Lock decision

The production evidence gate is now eligible for formal lock review.

Do NOT label the overall architecture externally as independently certified or externally audited. These are repository/GitHub Actions technical evidence results.

Next lock action:
- freeze the evidenced production authority and migration contract;
- prohibit legacy authority reactivation;
- record the final evidence commit;
- perform one final independent re-performance after the lock candidate is recorded;
- then declare FINAL LOCK only if that re-performance remains successful.
