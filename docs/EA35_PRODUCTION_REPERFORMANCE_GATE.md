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
