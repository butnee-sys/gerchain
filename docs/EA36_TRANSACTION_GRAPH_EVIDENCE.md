# EA-36 — Complete Transaction Graph & Independent Re-performance

Status: IN PROGRESS / NOT LOCKED

## Objective

EA-36 proves that one canonical value transaction remains one coherent transaction graph across:

transaction_id → operation → escrow_id → source → destination → amount → currency → Ledger movement → Escrow state → Witness → Outbox → Idempotency → Audit/evidence.

The objective is structural trust evidence, not assumption.

## Exact production evidence

Evidence SHA: `21496aa1991b891fb9fb0a186a83b1e948d4f863`

### PostgreSQL Production Runtime

Workflow run: `37709987832`

Result: SUCCESS

Verified job: `production-runtime`

Verified step: `Verify canonical production runtime boot` — SUCCESS

Artifact: `postgres-production-runtime-junit`
Artifact SHA-256:
`f789dcc49e134eebfeb4a8c006f11d4d014d03c1cb5a6ec4c577f2980c98d250`

### PostgreSQL Deep Value Truth

Workflow run: `37709987879`

Result: SUCCESS

Verified job: `production-postgresql-evidence`

Verified step: `Run deep value truth reconciliation on PostgreSQL` — SUCCESS

Artifact: `ea35-postgres-deep-reconciliation`
Artifact SHA-256:
`aebb2e0dd8e0015578ff05e626264e888be59134d6f364cea4ff7d8716357bc7`

## EA-36 invariants

1. No orphan canonical Ledger movement.
2. No committed value movement without matching Witness evidence.
3. No committed value movement without matching Outbox evidence.
4. No movement with mismatched operation or escrow aggregate.
5. No movement without durable idempotency evidence.
6. Integrity hash must bind transaction_id, operation, escrow_id, source, destination, amount and currency.
7. State-only LOCK evidence must not be falsely treated as a value movement.
8. Replay must not create a second movement, Witness or Outbox event.
9. Reuse of an idempotency key with a different request must fail.
10. Escrow state and canonical value movement must remain transactionally aligned.

## Current conclusion

The exact-SHA PostgreSQL runtime boot and deep value-truth reconciliation gates are both successful at the evidence SHA above.

This is strong EA-36 evidence, but it is not yet the final EA-36 lock because an independent re-performance must still be tied to the final current implementation SHA and the complete transaction graph must be independently re-executed after the latest changes.

## Lock rule

EA-36 may be locked only when:

- exact-SHA PostgreSQL transaction-graph re-performance is successful;
- independent re-performance is successful;
- no unexplained reconciliation issue exists;
- replay/conflict/rollback/recovery evidence is preserved;
- evidence references the final implementation SHA.

No GREEN/LOCK claim is made before those conditions are met.
