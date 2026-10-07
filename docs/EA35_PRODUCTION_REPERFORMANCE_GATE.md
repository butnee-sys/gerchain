# EA-35 Production Re-performance Gate

Status: IN PROGRESS / NOT LOCKED

## Purpose

This document defines the evidence gate for production PostgreSQL re-performance of the canonical GerChain value-flow runtime.

## Required evidence

1. ProductionRuntimeFactory constructs a PostgreSQL-only runtime.
2. Canonical production schema migration history is applied and checksum-stable.
3. Canonical Ledger is authoritative for production value movement.
4. Durable Escrow is authoritative for escrow state.
5. Witness, Outbox, and Durable Idempotency participate in the same canonical transaction boundary.
6. Deep Value Truth Reconciliation reports a matched graph after committed value operations.
7. Concurrent migration bootstrap is serialized and idempotent.
8. CI passes the relevant production/runtime and PostgreSQL concurrency gates at the exact tested revision.
9. Independent re-performance reproduces the evidence without relying on the implementation author.

## Current evidence

- Production entrypoint was corrected to construct ProductionRuntimeFactory as an instance and require canonical Ledger authority.
- Production factory initializes the canonical PostgreSQL migration path and asserts required canonical tables/history.
- A PostgreSQL production-factory boot integration test exists.
- The prior CI revision had two blocking failures: a stale malformed gerchain_runtime.py revision in the PR merge commit and a concurrent migration publication conflict at schema_version(version=2).
- Current migration code uses transaction-scoped advisory serialization plus conflict-safe schema-version publication.
- Current runtime source no longer contains the malformed escaped-line syntax seen in the prior CI run.

## Lock rule

No production lock may be declared until a fresh exact-SHA CI run passes the relevant gates and the PostgreSQL re-performance evidence is independently reproduced.

## Fresh exact-SHA evidence — 2026-10-07

Verified branch head: `933cff155a90b6ab4d2f16697e084499cabc07b6`.

The following GitHub Actions runs completed successfully at this exact revision:

- production-postgresql-reperformance — run 37684758322
- EAI PostgreSQL Production Proof — run 37684758266
- production-postgresql-gate — run 37684758298
- independent-postgresql-evidence — run 37684758179
- production-postgres — run 37684758308
- core-gates — run 37684758365
- CodeQL Advanced — run 37684758337
- CORE Operating Reconciliation — run 37684758263

Key execution evidence:

- PostgreSQL 16 service booted successfully.
- Production factory/schema verification passed.
- Production entrypoint boot against PostgreSQL passed.
- Concurrent migration bootstrap test passed.
- Deep reconciliation suite: 19 passed.
- PostgreSQL production smoke: passed.
- EAI production re-performance: passed.
- Independent persisted-value verification: passed.
- Production PostgreSQL value-flow gate: passed.

This establishes fresh exact-SHA PostgreSQL production evidence. It does not by itself waive remaining governance, access-control, disaster-recovery, or formal architecture-lock requirements.

**Current determination: PRODUCTION EVIDENCE VERIFIED / ARCHITECTURE LOCK NOT YET DECLARED.**
