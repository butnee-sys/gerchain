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


## Exact-SHA evidence checkpoint — 2026-11-01 — candidate `c0086ba9b5ab068d75631966635569037bed6598`

This is a bounded evidence checkpoint, not a final release candidate or lock approval. The original repository snapshot stated in the header is historical; this section records the later observed candidate and its run-scoped evidence.

### Same-SHA workflow results

All listed workflows completed successfully against `c0086ba9b5ab068d75631966635569037bed6598` (attempt 1):

- [Production Gate #41272250561](https://github.com/butnee-sys/gerchain/actions/runs/41272250561): success; artifact `13070002412`.
- [Production PostgreSQL Gate #41272250520](https://github.com/butnee-sys/gerchain/actions/runs/41272250520): success; artifacts `13069168501` and `13069512710`.
- [core-gates #41272250545](https://github.com/butnee-sys/gerchain/actions/runs/41272250545): success; artifact `13070310283`.
- [SHUUD/SANDBOX Product MVP Tests #41272250554](https://github.com/butnee-sys/gerchain/actions/runs/41272250554): success; artifact `13069727795`.
- [Independent Production Audit #41272250536](https://github.com/butnee-sys/gerchain/actions/runs/41272250536): success; artifact `13068968898`.
- [EAI PostgreSQL Re-performance #41272250524](https://github.com/butnee-sys/gerchain/actions/runs/41272250524): success.
- [PostgreSQL Production Re-performance #41272250570](https://github.com/butnee-sys/gerchain/actions/runs/41272250570): success; artifact `13069113745`.
- [FINAL EAI/CORE Exact-SHA Gate #41272250607](https://github.com/butnee-sys/gerchain/actions/runs/41272250607): success; artifact `13069667808`.
- [PostgreSQL Migration and Production Proof #41272250633](https://github.com/butnee-sys/gerchain/actions/runs/41272250633): success.

The successful workflow conclusions are not a blanket statement that every test in every suite executed: the retained JUnit files contain skipped tests, detailed below.

### Verified artifacts

**Production Gate — artifact `13070002412`:**
- `canonical-evidence-manifest.json` records `evidence_status=PASS_CANDIDATE`.
- `commit_sha` and `checked_out_head_sha` both equal `c0086ba9b5ab068d75631966635569037bed6598`.
- `source_hashes_complete=true`; 681 tracked source files are hashed.
- Per-file logs/JUnit: 1,206 test cases, 0 failures, 0 errors, 18 skipped; file-failure count 0.
- The replacement contract test `tests.test_final_lock_contract::test_shuud_workflows_are_separate_manual_entrypoints` passed.

**Production PostgreSQL Gate — artifact `13069168501`:**
- `migration-lifecycle-report.json`: `evidence_status=PASS_CANDIDATE`.
- `commit_sha` = `checked_out_head_sha` = `c0086ba9b5ab068d75631966635569037bed6598`.
- `source_hashes_complete=true`; `source_missing=[]`.
- 17 migration files, 17 applied versions (001–017), file/database checksums match, SHA-256 lengths valid.
- Lifecycle JUnit: 6 tests, 0 failures, 0 errors, 0 skipped.
- `migration-history.json` has contiguous versions 1–17 with non-null `applied_at`; PostgreSQL catalog/constraint evidence is retained.

**Canonical EAI regression — same Production PostgreSQL Gate artifact:**
- 1,212 tests, 0 failures, 0 errors, 18 skipped; `failure-count.txt=0`.
- The 18 skips are explicit environment-gated PostgreSQL/DEE tests in this broad regression job. They are not counted as passed by this JUnit. Separate PostgreSQL workflows supply overlapping migration, concurrency, boot, and re-performance evidence; the DEE PostgreSQL concurrent-rotation test remains unverified by this broad job.

**SHUUD/SANDBOX product workflow — artifact `13069727795`:**
- 108 tests, 0 failures, 0 errors, 1 skipped.
- The 20 SHUUD product cases corresponding to historical failure-register rows 2–21 all passed, including real-process restart (non-PostgreSQL), API lifecycle, timing, route registration, DEE protection, economics, KPI persistence, and sandbox configuration.
- `test_shuud_survives_postgres_process_restart` was skipped because `SHUUD_POSTGRES_DSN` was not configured. This is a separate unresolved PostgreSQL process-restart proof; do not mark it passed.

**core-gates and independent evidence:**
- core-gates artifact `13070310283`: core contract JUnit 56/56 passed; deep-reconciliation JUnit 24/24 passed.
- Independent audit artifact `13068968898` identifies the result as automated EAI evidence, not production-ready certification.
- PostgreSQL production re-performance artifact `13069113745` binds `github_sha`, `checked_out_sha`, and `tested_commit` to `c0086ba9b5ab068d75631966635569037bed6598`; migration versions/checksums and production boot are recorded. Its reconciliation is explicitly an empty-baseline check (zero movements, witnesses, outbox, idempotency, and escrows), not a populated live-transaction graph.
- Exact-SHA artifact `13069667808` has `git_status_porcelain=[]` and all 17 migration file hashes.

### Historical 21-failure disposition at this checkpoint

The 21 historical test cases are no longer observed as failures on `c0086ba9b5ab068d75631966635569037bed6598`: row 1 is superseded by the passing manual-entrypoint contract test in Production Gate JUnit; rows 2–21 pass in the isolated SHUUD/SANDBOX product JUnit. This is test-level regression evidence only, not a production certification. The separate PostgreSQL process-restart test remains skipped and open.

### Changes since this checkpoint and exact-SHA rule

Commit `0024117681c2bc004ed24e548f5526f3e8ab333e` adds `SHUUD_POSTGRES_DSN` to the isolated SHUUD product workflow so the skipped PostgreSQL restart test can execute. That commit is not covered by the `c0086ba9b5ab068d75631966635569037bed6598` artifacts. The documentation/evidence-register updates that follow will create a new candidate SHA; therefore every mandatory workflow and the PostgreSQL restart test must be rerun against the final documentation/code SHA, with run-scoped artifacts inspected again.

### Remaining mandatory production controls

The following are not closed by the current artifacts:
- physical legacy-authority write freeze and no-write proof;
- IAM/MFA, privileged access, and accountable approval;
- production observability, alerting, recovery, restart and no-duplicate-movement proof;
- production-like load/performance and application concurrency;
- backup/restore/DR drill and post-restore reconciliation with recovery objectives;
- release/branch governance and final exact-SHA evidence index;
- populated PostgreSQL value-truth reconciliation across a representative transaction graph;
- SHUUD PostgreSQL process-restart test (currently skipped; new workflow configuration awaits execution);
- independent review/acceptance and explicit authorized final-lock decision.

**Disposition remains: MASTER GATE = OPEN; PRODUCTION READY = NOT VERIFIED; FINAL LOCK = OPEN.**
