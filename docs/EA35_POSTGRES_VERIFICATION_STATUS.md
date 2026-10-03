# EA-35 PostgreSQL Verification Status

Date: 2026-09-28

## Scope

This record covers the production PostgreSQL authority gate for EA-35. It does not lock EAI or the wider architecture.

## Current source baseline

- Branch: `feat/ea21-transaction-aware-ledger`
- Current branch tip: `5ca4b84f37175f1beb097e55e7f779476cb65025`
- Production factory requires PostgreSQL, applies the canonical migration chain, runs `assert_canonical_production_schema`, configures `configure_canonical_ledger()`, and requires canonical-ledger authority.
- Production entrypoint constructs the factory through `ProductionRuntimeFactory.from_engine(...).create()`.
- Canonical schema guard requires Ledger, Escrow, Witness, Outbox and durable Idempotency structures plus the full escrow lifecycle and movement-integrity constraints.

## Prior execution evidence

A real PostgreSQL execution was previously completed successfully at exact SHA `890a78f36dcfe161e195da649b3cd124133d6535`.

Successful prior evidence included:
- PostgreSQL 16 service health;
- production factory construction;
- canonical Ledger authority;
- production entrypoint boot;
- canonical value-flow execution;
- REFUND/CANCEL re-performance;
- SETTLEMENT through Canonical Ledger;
- replay/idempotency;
- deep value-truth reconciliation.

That execution SHA is an ancestor of the current branch tip, but it is **not** the current branch tip. Therefore it remains historical execution evidence, not current-tip proof.

## Current execution gate

For current tip `5ca4b84f37175f1beb097e55e7f779476cb65025`:

- Workflow `production-postgresql-gate`, run `36381221710`: QUEUED.
- Workflow `production-postgres-gate`, run `36381222075`: QUEUED.
- Workflow `core-gates`, run `36381221698`: QUEUED.
- The branch therefore has no completed current-tip PostgreSQL production result at this inspection.

Queued is not PASS.

## Gate decision

**EA-35: IN PROGRESS / NOT LOCKED**

The architecture is source-verified and has historical real-PostgreSQL execution evidence, but the current tip must receive a completed exact-SHA PostgreSQL execution result before the evidence can be promoted to current-tip execution verification.

## Lock rule

No production lock may be declared from source inspection or historical ancestor execution alone.

Required current-tip evidence:
1. migration success;
2. canonical schema guard success;
3. production entrypoint boot;
4. canonical value-flow re-performance;
5. REFUND/CANCEL/SETTLEMENT verification;
6. deep value-truth reconciliation;
7. replay/idempotency verification;
8. no legacy value-authority fallback;
9. completed GitHub Actions result anchored to the current exact SHA.

After current-tip verification, perform independent re-performance/oracle review before the final production lock.


## Current exact-SHA verification trigger — 2026-10-03

This section records the current verification trigger. Historical successful SHA results are not promoted to current-tip evidence.

Required fresh execution on the resulting commit:
- Python syntax gate;
- PostgreSQL migration and canonical schema guard;
- production runtime construction;
- production entrypoint boot;
- canonical value-flow/replay;
- REFUND/CANCEL/SETTLEMENT;
- deep value-truth reconciliation;
- canonical EAI PostgreSQL gate;
- independent re-performance workflow where configured.

Status at trigger creation: **PENDING EXECUTION / NOT LOCKED**.

No GREEN or production lock is inferred from this trigger itself.
