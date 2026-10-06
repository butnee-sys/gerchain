# EA-35.13 — Production PostgreSQL Re-performance Evidence

Status: IN PROGRESS / NOT LOCKED

## Exact branch evidence

Branch: `feat/ea21-transaction-aware-ledger`

Latest proof commit:
`88bb6f1f1f6d29f4ef55b339079a312cda765554`

Earlier production-construction correction:
`e860f502f3e1a2d56fd873ad2faab7b1ab630740`

Canonical schema correction:
`d12af0cfc04214efe109bd0979006a9dd9448617`

## Verified statically

1. `ProductionRuntimeFactory` requires PostgreSQL.
2. Factory applies versioned migrations before runtime construction.
3. Factory runs `assert_canonical_production_schema()`.
4. Runtime is configured through `configure_canonical_ledger()`.
5. Runtime must satisfy `is_canonical_ledger_authoritative`.
6. Production entrypoint uses `ProductionRuntimeFactory.from_engine(...)`.
7. Canonical migration creates the six required production persistence tables.
8. Escrow lifecycle states are constrained to CREATED/FUNDED/LOCKED/RELEASED/REFUNDED/CANCELLED.
9. Canonical movement operations are constrained to FUND/RELEASE/REFUND/CANCEL/SETTLEMENT.
10. SETTLEMENT is explicitly unbound from an escrow; other value-flow operations require an escrow binding.
11. Movement integrity evidence is required and constrained to a 64-character hash.
12. Existing canonical movement rows without reconstructable integrity evidence cannot be silently promoted.

## Automated PostgreSQL proof

PR: #90 — EA-35.13 PostgreSQL production smoke gate.

The repository already contains a PostgreSQL service workflow and production test covering:
- production factory construction;
- canonical authority assertion;
- canonical account creation/read;
- FUND;
- LOCK;
- RELEASE;
- REFUND;
- CANCEL;
- deep value-truth reconciliation;
- movement/witness/outbox counts.

For commit `88bb6f1f1f6d29f4ef55b339079a312cda765554`, the GitHub Actions PostgreSQL/re-performance runs are currently **QUEUED**.

QUEUED is not evidence of success.

## Lock rule

EA-35 remains **IN PROGRESS / NOT LOCKED** until at least one fresh PostgreSQL run for the exact commit reaches SUCCESS and its job logs/evidence are inspected.

No GREEN claim is permitted before that point.
