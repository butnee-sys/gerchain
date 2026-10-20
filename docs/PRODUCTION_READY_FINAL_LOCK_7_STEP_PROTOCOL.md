# PRODUCTION READY FINAL LOCK — 7-Step Protocol

**Status:** FROZEN EXECUTION ORDER / IN PROGRESS / NOT LOCKED  
**Scope:** Canonical Architecture + EAI (Escrow as Infrastructure). Product layers are out of scope.  
**Architecture baseline:** `docs/DEE_ARCHITECTURE_FREEZE.md`

## Binding rules
1. Execute only these seven steps, in order. Do not skip, merge, reorder, or claim an unverified gate as PASS.
2. Preserve the frozen architecture. No silent architecture changes, second authoritative Ledger, second Witness Chain, second Escrow Engine, application-owned value truth, or bypass of Decision → Authorization → Release.
3. Every PASS requires reproducible evidence tied to an exact commit SHA. Missing/stale/ambiguous evidence = UNVERIFIED.
4. Fix failures only within the active step and existing architecture. If a frozen-architecture change is required, stop and request explicit approval.
5. The final source, migrations, tests, deployment evidence, and evidence index must identify the same candidate commit.

## Step 1 — Scope, architecture, and authority
Verify the canonical freeze identity; production factory/entrypoint alignment; Canonical Ledger authority; no legacy value-authority bypass; record baseline SHA and gaps. Exit: exact baseline and reviewed authority map.

## Step 2 — PostgreSQL schema and migrations
Run the versioned migration registry against clean PostgreSQL; rerun on the migrated database; verify migration history, tables, columns, unique keys, CHECK constraints, and expressions. ORM metadata creation is not a substitute for migrations. Exit: reproducible migration and schema evidence.

## Step 3 — Production boot and authority
Boot the actual production entrypoint against PostgreSQL. Prove readiness follows successful migration/schema checks; invalid URL, missing configuration, and schema drift fail closed; Canonical Ledger is authoritative and legacy stores are not. Exit: boot logs, negative tests, exact SHA.

## Step 4 — Operation correctness
Verify CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, account creation, escrow read, and balance read. Verify atomic value movement/state/witness/outbox/idempotency where applicable, safe replay, conflicting fingerprint rejection, and fail-closed authorization. Exit: operation acceptance matrix and PostgreSQL integration evidence.

## Step 5 — Deep value truth and recovery
Reconcile movement ↔ escrow ↔ witness ↔ outbox ↔ idempotency ↔ integrity hash. Test missing/mismatched/orphan evidence, state-only LOCK, rollback, incomplete operations, restart, outbox recovery, and retry without duplicate movement. Exit: clean and negative reconciliation reports plus recovery evidence.

## Step 6 — CI and independent re-performance
Run required tests/security checks and real PostgreSQL integration on the exact candidate SHA; validate production container/entrypoint and migrations; independently reproduce key tests. Empty check lists remain UNVERIFIED. Exit: exact-SHA run IDs/logs/artifacts and independent re-performance record.

## Step 7 — Final evidence and lock
Require explicit PASS for Steps 1–6, no unresolved critical/high issue, and evidence bound to the same candidate SHA. Publish evidence index, control matrix, residual risks, and explicit lock decision. Otherwise remain IN PROGRESS / NOT LOCKED.

## Initial gate status
| Step | Initial status |
|---|---|
| 1 | IN PROGRESS — verify current branch state |
| 2 | UNVERIFIED — real PostgreSQL evidence required |
| 3 | UNVERIFIED — real PostgreSQL boot evidence required |
| 4 | UNVERIFIED — production-path integration evidence required |
| 5 | IN PROGRESS — tests exist; PostgreSQL re-performance required |
| 6 | UNVERIFIED — exact-SHA CI and independent re-performance required |
| 7 | BLOCKED — depends on Steps 1–6 |

## First action
Inspect canonical freeze, current factory/entrypoint, migration registry, and exact-branch CI evidence. This document alone does not complete Step 1.

**Final lock invariant:** production readiness is an evidence-backed decision, not a documentation label.
