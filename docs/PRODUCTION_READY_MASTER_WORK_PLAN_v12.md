# PRODUCTION READY MASTER WORK PLAN v12

**Revision purpose:** consolidate the architecture-closure decision with the existing production final-lock work plan and current master-gate record.  
**Repository snapshot used to prepare this document:** `main` at `77a5db4c9722c1c1d20bb82ccd69e8cbe393dacf` (documentation snapshot only; not a verified production candidate SHA).  
**Disposition:** FINAL-LOCK CANDIDATE — BLOCKED / NOT LOCKED.  
**Scope:** GerChain fundamental architecture + EAI (Escrow as Infrastructure) + Canonical Ledger/PostgreSQL production boundary.  
**Explicit exclusions:** SHUUD and SHIID are separate applications and are not prerequisites for EAI final lock.

## 1. Decision and scope

The architecture-definition discrepancies A-01 (EXIM internal coordination), A-02 (DE Port), and A-03 (Family Port) are **CLOSED at the definition/boundary level** in `docs/ARCHITECTURE_EXTENSIONS_REVIEW_v1.md`. Their closure does not add a canonical layer, authority, adapter, ledger, escrow engine, witness chain, or settlement path.

The canonical architecture freeze remains authoritative and unchanged at baseline `10a408dc4a7821db85a9bc68cfccdb66a20b4dcf`. Do not edit or replace the freeze as part of this plan.

The latest repository master-gate record explicitly says **OPEN — FINAL LOCK NOT GRANTED**. The 7-step cumulative register also says gates 1–6 are not all locked and gate 7 is blocked. Therefore this revision does not promote any unverified gate to PASS or declare production readiness.

## 2. Canonical invariants — do not reopen without contradictory evidence

- Canonical Ledger is the only production value authority.
- Canonical Escrow is the only durable escrow-state authority.
- There is one authoritative Witness path and one production Outbox path.
- Value mutation, escrow transition, witness evidence, outbox evidence, and durable idempotency must satisfy the required transaction boundary.
- Production fails closed; no fallback to in-memory, SQLite, legacy release/balance stores, or application-owned balance mutation.
- Numbered migrations are the schema authority; runtime metadata initialization is not a substitute for migrations.
- A historical successful run is evidence only for its recorded SHA and tested scope.
- Queued, pending, missing, stale-SHA, mocked, or SQLite-only results are not a PASS for a live PostgreSQL gate.
- Do not repeat completed work unless fresh, specific contradictory evidence shows a regression.
- SHUUD/SHIID remain separate application scope.

## 3. Current gate register

Statuses below are carried forward from the repository's `docs/MASTER_GATE_PRODUCTION_FINAL_LOCK.md` and `docs/FINAL_LOCK_7_STEP_PROGRESS_REGISTER.md`; they are not newly executed test results.

| Gate | Carried status | Required closure evidence |
|---|---|---|
| Architecture / scope | Architecture freeze retained; A-01–A-03 definition closure recorded | Keep freeze unchanged; verify no contradictory authority path is introduced |
| Single value authority | Implemented; re-performance open | Exact-SHA runtime/database evidence showing Canonical Ledger only |
| Durable escrow lifecycle | Implemented; schema gate open | Clean PostgreSQL migrations and CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL lifecycle proof |
| Transaction integrity | Implemented; PostgreSQL proof open | Real PostgreSQL commit/rollback/replay/conflict/concurrency evidence across Ledger, Escrow, Witness, Outbox, and Idempotency |
| Deep value-truth reconciliation | Implemented; CI unverified | Exact-SHA PostgreSQL reconciliation report and negative-case evidence |
| Production entrypoint | Source correction retained; boot proof open | Exact-SHA production boot, readiness/health, fail-closed negative cases, clean shutdown |
| Legacy authority freeze | Documented; physical freeze open | No-write proof plus approved frozen/read-only, removed, or archived disposition |
| Security / privileged access | Open / evidence review required in existing master gate | Required IAM/MFA and privileged-access evidence, or a formally approved exception by the accountable authority |
| Observability / recovery | Open | Health/readiness, alerting, restart/recovery, and no-duplicate-movement evidence |
| Performance / concurrency | Open for current baseline | Reproducible production-like workload and concurrency evidence |
| Backup / restore / DR | Open | Restore drill, post-restore reconciliation, and recovery-objective evidence |
| CI / release governance | Unverified | Required checks on the exact release candidate; branch/release governance evidence |
| Independent re-performance | Open | Attributed independent re-performance with retained logs/results |
| Final evidence / lock approval | Open | One evidence index tied to one immutable candidate SHA and explicit authorized lock decision |

## 4. Mandatory PostgreSQL evidence gates

These are the three explicit PostgreSQL proof gates already specified in the repository's master plan; do not count them complete merely because test code or workflow configuration exists.

### PG-CONC-01 — Concurrent migration-runner execution
- Run two independent processes/connections against the same clean PostgreSQL database and invoke the canonical migration runner concurrently.
- Prove serialization, one row per migration version, expected SHA-256 checksums, no checksum conflicts, and a subsequent no-op run.
- Retain both process outputs and SQL results.

### PG-SCHEMA-02 — Actual post-migration schema verification
- Apply all 17 migrations to a clean PostgreSQL database.
- Query actual PostgreSQL catalogs for migration versions/checksums, tables, columns, indexes, foreign keys, CHECK/UNIQUE constraints, and applicable `pg_constraint.convalidated` values.
- Prove checksums match the migration SQL and a second run changes neither migration registry nor schema.
- Retain raw catalog output.

### PG-TRUTH-03 — Deep value-truth reconciliation on PostgreSQL
- Seed a canonical value-flow graph in PostgreSQL and execute the real `deep_reconcile_value_truth(session)`.
- Verify movement-to-escrow, event/operation binding, witness, outbox, completed durable idempotency, and recomputed integrity hash.
- Prove the clean graph passes and deliberately corrupted witness/outbox/idempotency/escrow/integrity records fail with expected issue codes.
- Retain actual PostgreSQL reports and negative-test outputs.

For all three gates, retain the candidate SHA, PostgreSQL version, command/process identifiers, migration version/checksum rows, schema/constraint dump, clean and corrupted reconciliation outputs, workflow run/job IDs, logs, and artifact references. Empty, queued, stale-SHA, mocked, or SQLite-only evidence is UNVERIFIED.

## 5. Exact-SHA and evidence control

1. Select one release-candidate commit only after the intended documentation/code changes are present.
2. Bind each required workflow run, job conclusion, log, artifact, migration output, reconciliation report, and independent result to that exact SHA.
3. Reuse historical evidence only where the exact SHA and coverage are demonstrably applicable; do not treat an ancestor run as proof of a later commit.
4. Inspect existing failed runs by exact run/job/failed step and classify them as a genuine defect, path/routing issue, transient/environment failure, stale/duplicate alert, or evidence-only gap before taking action.
5. Do not rerun successful work simply to create duplicate evidence; run only missing or actionable gates.
6. Do not publish a completion percentage unless a versioned weighted denominator and item-level evidence are retained.

## 6. Final-lock exit criteria

Final lock may be granted only when all mandatory technical and governance gates required by the current master gate have evidence on one exact candidate SHA, no mandatory gate is queued/pending/missing/failed, PostgreSQL migration/schema/concurrency/value-truth proofs are retained, the independent re-performance is recorded, and the accountable authority has made an explicit decision.

A documentation merge alone does not satisfy these criteria. If a required control is excepted, the accountable authority must explicitly approve and record that exception; the implementation team must not silently waive it.

## 7. Current disposition

**Architecture-definition discrepancies A-01–A-03: CLOSED.**  
**Canonical architecture freeze: UNCHANGED.**  
**Production master gate: OPEN.**  
**PRODUCTION READY / FINAL LOCK: NOT GRANTED by this plan revision.**

This is an evidence-closure plan, not authorization to redesign, rewrite, or broaden scope. Proceed only with the remaining unverified gates and retain the no-repeat rule.
