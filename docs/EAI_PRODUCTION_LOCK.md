# EAI Production Lock Record

Status: **LOCKED**

Scope: **EAI — Escrow as Infrastructure**

This lock applies only to the canonical EAI production infrastructure and does not authorize or lock downstream product/application layers.

## Exact evidence commit

f3dc16933593ae2dff5ec5e7e1d4df3d65ce979c

## Production evidence

All gates below completed successfully against the exact evidence commit:

- PostgreSQL production gate: PASS
- Production PostgreSQL boot: PASS
- Canonical persistence table gate: PASS
- Canonical Ledger movement and replay gate: PASS
- PostgreSQL migration concurrency gate: PASS
- Deep value-truth reconciliation suite: PASS
- EAI PostgreSQL production proof: PASS
- Independent persisted-value verification: PASS
- Production PostgreSQL re-performance: PASS

## Locked invariants

1. Canonical Ledger is the authoritative value-movement boundary.
2. Canonical Escrow is the durable escrow state authority.
3. Escrow value movement occurs only through the canonical Ledger transaction boundary.
4. Decision, Authorization, and Release remain distinct controls.
5. Witness is evidence, not a second authoritative value chain.
6. Outbox is the single production event-delivery path.
7. Durable Idempotency prevents replayed value duplication and detects request conflicts.
8. Deep reconciliation binds movement, escrow, witness, outbox, idempotency, and integrity evidence.
9. PostgreSQL is the production persistence boundary.
10. Legacy/in-memory value stores are not production authority.
11. Production entrypoint fails closed unless canonical PostgreSQL authority is established.
12. No downstream product/application layer may mutate EAI authoritative truth directly.

## Trust condition

EAI moves value only when structural trust is established:

**Truth → Condition → Verification → Decision → Authorization → Execution → Evidence → Audit → Recovery**

## Lock rule

Any change to a locked invariant requires an explicit architecture/change proposal and a new production re-performance before the lock can remain valid.
