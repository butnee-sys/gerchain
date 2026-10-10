# EA-35.13 — PostgreSQL Production Re-performance Gate

Status: IN PROGRESS / NOT LOCKED

Required evidence:
- PostgreSQL 16 service
- canonical production schema migration + schema guard
- ProductionRuntimeFactory canonical ledger authority
- durable account creation and read
- FUND → LOCK → RELEASE
- RELEASE replay/idempotency
- REFUND
- CANCEL
- SETTLEMENT
- deep value-truth reconciliation
- exact-SHA CI evidence
- independent re-performance

No production lock is valid until the exact branch commit has fresh passing CI evidence for the production PostgreSQL gate.
