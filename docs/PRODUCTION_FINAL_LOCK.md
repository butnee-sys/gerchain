# PRODUCTION FINAL LOCK — Evidence Register

**Repository:** `butnee-sys/gerchain`  
**Working branch:** `feat/ea21-transaction-aware-ledger`  
**Purpose:** Record evidence-based production gates. This register does not promote a gate to CLOSED without exact-commit runtime evidence.

## Gate 1 — PostgreSQL migration-history serialization and checksum integrity

**Implementation status:** FIX APPLIED IN CURRENT BRANCH SOURCE  
**Verification status:** OPEN — fresh exact-SHA PostgreSQL re-performance required  
**Production lock status:** NOT LOCKED

### Failure evidence reviewed
GitHub Actions PostgreSQL Concurrency run `36542458201` (run #1618) failed with **1 failed, 5 passed**. The failure was:

`test_migrations_are_serialized_and_checksum_is_stable`  
`psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "schema_version_pkey"`  
`Key (version)=(2) already exists.`

This run is historical evidence against the code at the commit tested by that run; it is not proof that the current branch still fails or that the current branch passes.

### Current source correction to be verified
The current `postgres/migrations.py` implementation now:
1. Acquires a session-scoped PostgreSQL advisory lock for the complete migration batch.
2. Applies schema DDL and migration-history publication within the controlled transaction.
3. Establishes a unique index on `schema_version(version)` after rejecting conflicting checksum history and safely collapsing only identical duplicate history.
4. Publishes each version with one conflict-safe `INSERT ... ON CONFLICT ... DO UPDATE ... WHERE schema_version.checksum = EXCLUDED.checksum RETURNING checksum` statement.
5. Fails closed if the published checksum is absent or differs from the expected SHA-256 digest.

### Closure criteria
Gate 1 may be marked **CLOSED** only when a fresh PostgreSQL Actions run tied to the exact commit containing this register demonstrates all of the following:
- two independent PostgreSQL backend connections race a genuinely empty disposable database;
- both migration runners finish without error;
- exactly one `schema_version` row exists per canonical version, with no gaps;
- both runners and the final database observe the same ordered version/checksum history;
- each checksum is a 64-character SHA-256 hex digest and is stable on re-run;
- the migration test job concludes SUCCESS.

### Current decision
**Gate 1 is not yet closed.** Source inspection confirms the conflict-safe publication path is present, but source inspection is not runtime evidence. Do not mark EAI or the overall production architecture production-ready until the exact-SHA PostgreSQL gate passes and its run URL/SHA are recorded here.

## Final lock rule

No downstream product-layer readiness, CORE-only result, or source-code presence substitutes for the complete production evidence chain. The overall architecture and EAI remain **IN PROGRESS / NOT LOCKED** until all required gates are evidenced, independently re-performed, and formally accepted.


---

## Master Work Plan — Step 1: Inventory / Map

**Work-plan step status:** CLOSED — FINAL LOCKED (inventory scope only)  
**Evidence:** `docs/PRODUCTION_GATE_01_INVENTORY_MAP.md`  
**Inventory evidence commit:** `c6ec9e01af56ffbc8be7dd7df67d2067b8c8d2da`  
**Overall production lock:** NOT LOCKED

### Completed inventory

The repository inventory and dependency map now explicitly record:
- canonical architecture layers and adapter boundaries;
- DEE, G3, NEF + GerChain, EXIM, I2B, MultiConnector and PDEIZ responsibilities;
- production entrypoint, factory, runtime and non-production/legacy entrypoints;
- authoritative Ledger, Escrow, Witness, Outbox, Idempotency and reconciliation boundaries;
- operation routing for CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, READ and recovery;
- migration registry, schema bootstrap and production schema guard;
- legacy/alternate value stores and previously identified bypass paths;
- outstanding migration/restart proof, legacy-store physical freeze, IAM/MFA, branch governance, CI and independent review gaps.

### Acceptance boundary

This closes the **Master Work Plan's Step 1 — Inventory / Map** as a repository/source inventory deliverable and authorizes progression to **Step 2 — Error / Duplicate / Excess**. It does not claim that the migration-history race gate above is closed, does not claim current-tip PostgreSQL execution success, and does not grant overall production readiness.

**Master Work Plan Step 1: CLOSED.**  
**Next work-plan step: Step 2 — Error / Duplicate / Excess.**  
**Overall fundamental architecture + EAI: IN PROGRESS / NOT LOCKED.**
