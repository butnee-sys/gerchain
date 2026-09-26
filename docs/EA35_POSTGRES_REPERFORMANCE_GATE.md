# EA-35 PostgreSQL Re-Performance Gate

Status: IN PROGRESS / NOT LOCKED

## Required evidence

The production PostgreSQL gate must verify all of the following on the exact tested commit:

1. ProductionRuntimeFactory constructs a PostgreSQL runtime.
2. Canonical Ledger authority is established.
3. production_entrypoint.py boots against PostgreSQL and remains alive until controlled termination.
4. FUND -> LOCK -> RELEASE executes against the Canonical Ledger.
5. REFUND uses the authoritative refund destination.
6. FUNDED CANCEL reverses to the authoritative original sender.
7. Witness, Outbox, and durable Idempotency evidence are persisted.
8. Deep value-truth reconciliation passes.
9. No legacy value authority is used by the production runtime.
10. The workflow result is available as fresh GitHub Actions evidence for the exact commit.

No GREEN or production lock may be declared from source inspection alone.

## Authority invariant

No production value movement may mutate a balance outside
gerchain_ledger_accounts / gerchain_ledger_movements through the
transaction-aware PostgreSQLAtomicLedger boundary.

## Lock condition

EA-35 remains NOT LOCKED until fresh PostgreSQL workflow evidence exists
for the exact release candidate commit and the complete evidence chain
has been independently re-performed.
