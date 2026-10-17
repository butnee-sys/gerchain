# EA-35 Production PostgreSQL Re-performance

Status: IN PROGRESS / NOT LOCKED

This document is an evidence gate, not an attestation. Production PostgreSQL re-performance must pass on the exact branch tip before EA-35 can be locked.

Required evidence:
- PostgreSQL runtime boot establishes Canonical Ledger authority.
- Canonical Ledger, Escrow, Witness, Outbox, and durable Idempotency persistence are present.
- FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT and canonical READ execute against production PostgreSQL.
- Replay is idempotent and does not duplicate value movement.
- Deep Value Truth Reconciliation remains matched after each value operation.
- No legacy value authority is used by the production runtime.
- Exact-SHA GitHub Actions evidence is captured.

Until all gates pass, no GREEN or production lock is declared.
