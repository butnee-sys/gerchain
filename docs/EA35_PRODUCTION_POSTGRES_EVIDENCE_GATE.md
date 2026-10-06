# EA-35 Production PostgreSQL Evidence Gate

Status: IN PROGRESS / NOT LOCKED

This document defines the evidence required before the EAI production boundary can be locked.

## Required executable evidence

1. PostgreSQL 16 service is healthy.
2. Canonical production schema versions 1 through 11 apply successfully and idempotently.
3. ProductionRuntimeFactory establishes Canonical Ledger authority.
4. Required canonical tables and columns exist.
5. Canonical Ledger movement is durable and idempotent.
6. FUND, LOCK, RELEASE, REFUND, CANCEL and SETTLEMENT execute against canonical persistence.
7. State-only LOCK produces witness/outbox evidence without a value movement.
8. Deep Value Truth Reconciliation reports matched.
9. Independent persisted-value verification reproduces the result from raw PostgreSQL facts.
10. Production entrypoint boots only with PostgreSQL and fails closed on incomplete canonical schema.

## Lock rule

No production GREEN or EAI LOCK is declared from source inspection alone. A fresh GitHub Actions run at the exact tested commit must provide successful PostgreSQL evidence.

## Current evidence

Executable workflows:
- .github/workflows/production-postgresql-gate.yml
- .github/workflows/production-postgres.yml
- .github/workflows/independent-postgresql-evidence.yml

Until a fresh exact-SHA run is observed, this gate remains NOT LOCKED.