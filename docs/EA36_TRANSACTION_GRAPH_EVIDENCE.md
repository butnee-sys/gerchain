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

Independent EA-36 re-performance is now successful on the current implementation SHA `b3fb4f94b57e6026f92573d86a702dec995a5088`.

## Lock rule

EA-36 may be locked only when:

- exact-SHA PostgreSQL transaction-graph re-performance is successful;
- independent re-performance is successful;
- no unexplained reconciliation issue exists;
- replay/conflict/rollback/recovery evidence is preserved;
- evidence references the final implementation SHA.

No GREEN/LOCK claim is made before those conditions are met.


## EA-36 independent re-performance — SUCCESS

Implementation SHA: `b3fb4f94b57e6026f92573d86a702dec995a5088`

Workflow run: `37743459462`

Job: `ea36-postgresql`

Result: **SUCCESS**

The gate executed against a real PostgreSQL 16 service and completed the independent transaction-graph test successfully.

Verified graph:

- transaction_id
- operation
- escrow_id
- source
- destination
- amount
- currency
- integrity hash
- canonical Ledger movement
- durable Escrow state
- Witness
- Outbox
- durable Idempotency
- deep value-truth reconciliation
- exact replay without duplicate evidence
- conflicting replay rejection

Artifact: `ea36-postgresql-reperformance`

Artifact SHA-256:
`10e7057e6b9331e7cf7abeb23ad6dc7b290ca4bb721d7ef51a741ea137ce09d0`

The earlier false-positive PostgreSQL gate was also identified: the previous job executed the reconciliation test against its SQLite in-memory helper despite exposing a PostgreSQL URL. EA-36 closes that evidence-quality gap by using a dedicated test that rejects non-PostgreSQL URLs and executes directly against the PostgreSQL service.
