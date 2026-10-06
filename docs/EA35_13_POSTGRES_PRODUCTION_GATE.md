# EA-35.13 PostgreSQL production gate evidence

Status: IN PROGRESS / NOT LOCKED

## Verified external CI evidence
Commit: e860f502f3e1a2d56fd873ad2faab7b1ab630740
Date observed: 2026-09-29

PostgreSQL Concurrency run 36542458201 failed:
- 5 tests passed, 1 failed.
- Failure: concurrent migration test raised duplicate schema_version(version=2).
- PostgreSQL logs confirm duplicate primary-key insertion for version 2.

core-gates run 36542458205 failed:
- test collection stopped on SyntaxError in services/gerchain_runtime.py.
- The affected commit contained literal escaped newline sequences in the fund method.

## Current branch correction status
The current branch contains:
- conflict-safe migration history handling in postgres/migrations.py;
- canonical ProductionRuntimeFactory construction;
- production_entrypoint using ProductionRuntimeConfig + factory instance;
- GerchainRuntime canonical ledger authority configuration.

## Gate rule
No production GREEN/LOCK is declared until a fresh exact-SHA PostgreSQL run passes migration concurrency and runtime collection, followed by canonical value-flow and deep value-truth re-performance.
