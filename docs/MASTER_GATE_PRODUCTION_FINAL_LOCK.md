# MASTER GATE — PRODUCTION READY FINAL LOCK

**Status: OPEN — FINAL LOCK NOT GRANTED**  
**Scope:** Canonical GerChain/EAI production infrastructure and overall foundational architecture.  
**Explicit exclusions:** SHUUD and SANDBOX are separate product MVPs, not components of GERCHAIN EAI. Their product behavior and product test failures are outside this EAI assurance boundary and must not reopen or contaminate GerChain/EAI gates. Only a separately specified EAI adapter/contract test may remain in scope when it directly verifies a frozen EAI interface; no SHUUD/SANDBOX product lifecycle test is an EAI acceptance criterion.

## 1. Scope and invariants

This register consolidates previously closed gates without reopening them solely because the Master Gate is being introduced. A prior gate remains closed at its recorded evidence baseline unless a concrete regression, changed dependency, or new contradictory evidence is identified.

Production authority invariants:
- Canonical Ledger is the only production value authority.
- Canonical Escrow is the only durable escrow-state authority.
- One authoritative Witness path and one production Outbox path.
- Value mutation, escrow transition, witness evidence, outbox evidence, and durable idempotency must share the required transaction boundary.
- Production must fail closed; no fallback to in-memory, SQLite, ReleaseAccount, AccountBalance, or application-owned balance mutation.
- Unknown or unverified evidence is not a pass.
- This Master Gate does not change the frozen canonical architecture.

## 2. Previously closed gates — retained, not reopened

The following are retained as previously recorded repository evidence and are not reopened by this document alone:

| Gate | Recorded disposition | Scope note |
|---|---|---|
| Canonical architecture freeze | FROZEN | Existing freeze record remains authoritative |
| CORE atomic release/idempotency | GREEN in existing CORE audit record | Retain prior evidence; do not generalize beyond its tested scope |
| CORE PostgreSQL concurrency | GREEN in existing CORE audit record | Retain prior evidence; not a substitute for the current EAI production re-performance |
| CORE abandoned PROCESSING recovery | GREEN in existing CORE audit record | Retain prior evidence |
| CORE reconciliation / CodeQL controls | GREEN in existing CORE audit records | Historical evidence remains scoped to its exact baseline |
| SHUUD / SANDBOX isolation | OUT OF SCOPE / SEPARATE PRODUCT MVPs | No SHUUD or SANDBOX product gate is part of EAI final lock |

A retained historical GREEN does not automatically prove the latest working branch or current production deployment. Evidence remains tied to its recorded commit and test scope.

## 3. Master Gate checklist

| ID | Gate | Current status | Closure evidence required |
|---|---|---|---|
| MG-01 | Canonical architecture and scope | RETAINED | Frozen architecture reference; no unauthorized change |
| MG-02 | Single value authority | IMPLEMENTED / RE-PERFORMANCE OPEN | Runtime and database evidence showing Canonical Ledger only |
| MG-03 | Durable escrow lifecycle | IMPLEMENTED / SCHEMA GATE OPEN | PostgreSQL migration and lifecycle tests for CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL |
| MG-04 | Transaction integrity | IMPLEMENTED / POSTGRESQL PROOF OPEN | Real PostgreSQL commit/rollback/replay/conflict tests across Ledger/Escrow/Witness/Outbox/Idempotency |
| MG-05 | Deep value-truth reconciliation | IMPLEMENTED / CI UNVERIFIED | Exact-SHA passing test and clean PostgreSQL reconciliation report |
| MG-06 | Production entrypoint | CORRECTED / BOOT PROOF OPEN | Exact-SHA image build and real PostgreSQL startup/readiness evidence |
| MG-07 | Legacy authority freeze | DOCUMENTED / PHYSICAL FREEZE OPEN | Verify no production route can write legacy stores; negative tests |
| MG-08 | Security and privileged access | OPEN / EVIDENCE REVIEW REQUIRED | Current IAM/MFA and privileged-access evidence |
| MG-09 | Observability and operational recovery | OPEN | Health/readiness, alerting, restart/recovery and no-duplicate-movement evidence |
| MG-10 | Performance and concurrency | OPEN FOR CURRENT BASELINE | Reproducible production-like workload evidence |
| MG-11 | Backup/restore and disaster recovery | OPEN | Restore drill, reconciliation after restore, documented recovery objectives |
| MG-12 | CI/release governance | UNVERIFIED | Passing required checks for exact final commit; protected-branch/release evidence |
| MG-13 | Independent re-performance | OPEN | Independent execution and signed/retained results |
| MG-14 | Final evidence index and approval | OPEN | All required evidence mapped to exact commit/deployment; authorized final approval |

## 4. Production entrypoint correction

The production entrypoint and runtime factory were corrected in commit:
`e860f502f3e1a2d56fd873ad2faab7b1ab630740`

The entrypoint now constructs `ProductionRuntimeConfig`, instantiates `ProductionRuntimeFactory`, and calls the instance `create()` method. The factory configures the Canonical Ledger boundary rather than the legacy PostgreSQL release authority.

**This is a source correction, not proof of successful production boot.** The factory's metadata initialization is not a substitute for versioned, reviewed database migrations.

## 5. Final-lock rule

Do not label the system “PRODUCTION READY — FINAL LOCKED” until MG-02 through MG-14 have closure evidence at the exact release candidate, all mandatory checks are verified, PostgreSQL re-performance is successful, and independent re-performance is retained.

Any failure in a mandatory gate keeps the final lock OPEN. A successful historical gate is preserved at its original evidence baseline; it is only reopened if a specific regression or changed assumption is demonstrated.

## 6. Current final disposition

**MASTER GATE: OPEN**  
**PRODUCTION READY FINAL LOCK: NOT GRANTED — EVIDENCE GATES REMAIN OPEN**  
**SHUUD / SANDBOX: SEPARATE PRODUCT MVPs — OUT OF EAI SCOPE**  
**Canonical architecture freeze: unchanged.**


## Candidate evidence checkpoint — 2026-10-30

Current branch candidate reviewed: `2c4c6dd0871a688e4f3f7dc354295020d2a5da8a`.

Verified at this candidate:
- SHUUD/SANDBOX product MVP JUnit: 108 tests, 0 failures, 0 errors, 1 skipped (PostgreSQL process-restart test skipped because `SHUUD_POSTGRES_DSN` was not configured); 20 historical rows #2–#21 individually pass on this SHA.
- EAI core JUnit: 56/56 passed; deep value reconciliation JUnit: 24/24 passed.
- 17 migration files and 17 applied migration-history rows are retained in the EAI PostgreSQL re-performance evidence.
- PostgreSQL production re-performance reports SHA equality and successful production boot, but its evidence status is only `COLLECTED_PENDING_VERIFICATION`; its reconciliation is an empty-baseline check, not a populated live-transaction proof.
- The full Production Gate and Production PostgreSQL Gate are still running, and core-gates is pending at the time of this checkpoint. Row #1 of the historical 21-test register is therefore not closed.

The old SHA-mismatched artifact remains quarantined. The tracked `docs/production-master-gate-manifest.json` is a source template with no embedded candidate SHA; run-specific manifests must remain in run-scoped artifacts and must be validated against their run metadata. The historical certificate JSON/PDF remain explicitly withdrawn as current certification.

Before selecting a release candidate, finish the current runs and reconcile all retained artifacts. Then make one documentation/evidence-register commit, freeze its resulting SHA, and rerun every mandatory gate on that exact SHA. Do not combine evidence from different candidate SHAs.

Outstanding production controls remain: legacy authority-store write freeze, IAM/MFA and privileged access, observability/recovery/no-duplicate movement, production-like performance/concurrency, backup/restore/DR, independent re-performance, complete evidence index, and explicit authorized approval.

**MASTER GATE = OPEN; PRODUCTION READY = NOT VERIFIED; FINAL LOCK = OPEN.**


## Exact-SHA evidence checkpoint — 2026-10-31 — candidate `8695758751a8d484aa41651add4f6cf5322ef160`

This checkpoint supersedes the 2026-10-30 candidate snapshot above for current branch status. It does not grant or imply production readiness.

### Candidate identity and workflow results

- Branch: `fix/withdraw-unverified-production-certificate`
- Candidate SHA: `8695758751a8d484aa41651add4f6cf5322ef160`
- Commit: [8695758751a8d484aa41651add4f6cf5322ef160](https://github.com/butnee-sys/gerchain/commit/8695758751a8d484aa41651add4f6cf5322ef160)
- PR #111 remains open. The previous `d9c8af8...` run results are not evidence for this newer SHA.

Same-SHA workflow results observed:
- [Production Gate run 41212630458](https://github.com/butnee-sys/gerchain/actions/runs/41212630458): **FAILURE**.
- [Production PostgreSQL Gate run 41212630656](https://github.com/butnee-sys/gerchain/actions/runs/41212630656): **FAILURE**.
- [core-gates run 41212630511](https://github.com/butnee-sys/gerchain/actions/runs/41212630511): pending/no completed job at review time.
- [Independent Production Audit run 41212630630](https://github.com/butnee-sys/gerchain/actions/runs/41212630630): workflow success; audit metadata binds to this SHA and PostgreSQL 16. This is a bounded audit, not closure of all master gates.
- [Production Readiness Gates run 41212630519](https://github.com/butnee-sys/gerchain/actions/runs/41212630519): both migration/boot and value-truth jobs succeeded.
- [Canonical PostgreSQL Migration Gate run 41212630582](https://github.com/butnee-sys/gerchain/actions/runs/41212630582): success.
- [FINAL EAI/CORE Exact-SHA Gate run 41212630654](https://github.com/butnee-sys/gerchain/actions/runs/41212630654): success.
- [CI Test Suite run 41212630702](https://github.com/butnee-sys/gerchain/actions/runs/41212630702): success.
- DEE Security Gate, PostgreSQL concurrency/migration, migration idempotency, and EAI/PostgreSQL re-performance workflows also report success on this SHA.

### Exact-SHA failure evidence

**Production Gate artifact:** [run 41212630458](https://github.com/butnee-sys/gerchain/actions/runs/41212630458), artifact `13047322337`, file `canonical-evidence-manifest.json`.
- `commit_sha` = `checked_out_head_sha` = candidate SHA.
- `source_hashes_complete=true`; 681 source files hashed.
- `evidence_status=INCOMPLETE_OR_FAILED`.
- `gate_file_failure_count=7`.
- JUnit totals: 4 failures, 1 error, 18 skipped, across 313 suites.
- Failing file-level evidence includes:
  1. `tests/production/test_production_runtime_postgres_smoke.py`: second PostgreSQL scenario timed out during fixture setup at 300 seconds while truncating shared tables.
  2. `tests/production/test_runtime_postgres_smoke.py`: `runtime.create_account(...)` returned `None`; test expected a balance result.
  3. `tests/test_final_lock_contract.py`: workflow source no longer contains the expected explicit exclusions preserving `test_shuud_boundary.py` and `test_shuud_exim_boundary.py`.
  4. `tests/test_production_postgres.py`: value-flow test could not find the expected ledger account row (`NoResultFound`).
  5. `tests/test_production_postgres_boot.py`: stale test assertion expects migration version 12, but the canonical chain is now version 17.
- The gate reports seven failing files; the retained artifact excerpt exposes the five named JUnit cases above. The remaining two file-level failures must be reconciled from the complete retained per-file logs before this register is considered complete.

**Production PostgreSQL Gate artifact/logs:** [run 41212630656](https://github.com/butnee-sys/gerchain/actions/runs/41212630656), artifacts `13047093063` and `13047456980`.
- Canonical EAI regression JUnit: 1,212 tests, 1,180 passed, 10 failed, 4 errors, 18 skipped; duration 695.043 seconds.
- Seven persistence/production cases fail with `DuplicateObject` because `gerchain_movement_amount_check` already exists while production runtime initialization applies migrations to a database whose schema was also created/altered by test setup. This is a real migration/bootstrap idempotency defect to resolve, not a pass.
- One test has a migration-count expectation of 12 while the current canonical inventory is 17.
- One value-flow test has a missing ledger-account row (`NoResultFound`).
- Two production PostgreSQL smoke tests timed out at 300 seconds.
- The final evidence-generation step raised `KeyError: GERCHAIN_EVIDENCE_DATABASE_URL`; therefore no valid current-SHA lifecycle evidence report was produced by this run. Do not reuse the older `d9c8af8...` report as a substitute.
- Segmented regression failure count is 1. It must be examined and dispositioned; do not treat the SHUUD/SANDBOX scope note as evidence that these EAI regressions passed.

### Required remediation register for this candidate

| Ref | Observed defect | Requirement / acceptance criterion | Required action and proof |
|---|---|---|---|
| PG-01 | Migration 010 re-adds an already-existing `gerchain_movement_amount_check` during production factory boot | Production boot and migration replay must be safe on supported pre-existing schema states | Reproduce with the exact CI fixture; correct migration ordering/legacy fixture ownership or make migration robust without weakening the check; test fresh install, upgrade, and repeated boot |
| PG-02 | Migration lifecycle evidence step lacks `GERCHAIN_EVIDENCE_DATABASE_URL` | Evidence report must be generated and retained from a dedicated fresh PostgreSQL database | Fix workflow environment propagation/order; assert variable exists before use; produce JSON + detached SHA-256 + JUnit on the candidate SHA |
| PG-03 | Two smoke-test setup/runtime defects: shared-table truncate timeout and `create_account` returns `None` | Production account creation and test isolation must be deterministic, bounded, and auditable | Separate DB fixtures or scoped cleanup; inspect canonical runtime return contract; correct implementation/test expectation based on API contract; targeted and full rerun |
| PG-04 | Production value-flow test cannot find seeded account | Atomic ledger transfer must operate on the same durable account/session state | Trace account creation/session transaction boundary; prove source/destination rows exist before transfer; rerun end-to-end PostgreSQL flow and reconciliation |
| PG-05 | Test expects schema version 12 while canonical migration inventory is 17 | Tests must assert the current canonical migration contract, not a historical count | Update stale assertion only after verifying the exact canonical list 001–017; test the maximum version and exact ordered history |
| PG-06 | Core workflow contract test disagrees with actual SHUUD boundary-test selection | EAI scope must exclude SHUUD product tests while retaining explicitly required boundary contracts | Align workflow selection and contract test; prove both boundary tests execute and product suites remain excluded |
| PG-07 | Two 300-second PostgreSQL smoke-test timeouts | Required PostgreSQL lifecycle/recovery proof must complete within a declared bounded duration | Identify lock contention/fixture deadlock; ensure fixture cleanup does not contend with test-held connections; targeted rerun with lock diagnostics |
| PG-08 | Seven Production Gate file failures; only five named JUnit cases visible in inspected artifact excerpt | Every file-level failure must have a named case, cause, requirement mapping, and verified resolution | Reconcile all seven file logs and JUnit files; no blanket waiver |
| PG-09 | Historical 21-failure register was created on an earlier candidate | No failure may be called resolved solely because the candidate changed | Map all 21 historical cases to current test inclusion/exclusion and current results; each row gets FIXED + same-SHA PASS, OUT-OF-SCOPE + owner/contract proof, or OPEN |
| PG-10 | Current `core-gates` result not completed at review | Mandatory core assurance must pass on exact final SHA | Obtain completed passing run after all source/evidence changes; retain complete logs and artifact |

### Evidence integrity warning

A previously downloaded artifact from run `39849400071` carries commit SHA `d9c8af8d7b9498ff6c814543112a06d11f73602b`, not this candidate. It cannot substantiate the `8695758...` candidate. The current Production Gate manifest has complete source hashes (681 files) but is explicitly `INCOMPLETE_OR_FAILED`; the current PostgreSQL lifecycle report is missing because evidence generation failed. The successful current-SHA migration and independent audit jobs do not replace these failed/missing artifacts.

### Next work sequence

1. Reconcile all seven Production Gate file failures and all 10 + 4 EAI regression failures/errors into a case-level register; include the earlier 21 cases and their current same-SHA status.
2. Fix the migration duplicate-constraint defect and the missing evidence-database environment propagation.
3. Fix or correct the stale migration-version assertion, account-creation result contract, value-flow row/session issue, workflow boundary selection, and PostgreSQL fixture timeout.
4. Run focused regression tests, then the full mandatory suites on one frozen candidate SHA.
5. Produce a current-SHA `PASS_CANDIDATE` migration lifecycle report, detached report checksum, full source hash inventory, and JUnit with zero failures/errors.
6. Complete independent re-performance and all open operational/security/recovery/performance/DR/release-governance controls at that same SHA; obtain authorized approval.

**Disposition at this checkpoint: MASTER GATE = OPEN; PRODUCTION READY = NOT VERIFIED; FINAL LOCK = OPEN.**


## Exact-SHA evidence checkpoint — 2026-11-01 — candidate `c0086ba9b5ab068d75631966635569037bed6598`

This checkpoint supersedes the earlier 2026-10-31 candidate checkpoint for the evidence listed below. It does not change the Master Gate decision.

### Verified same-SHA runs

- Production Gate [41272250561](https://github.com/butnee-sys/gerchain/actions/runs/41272250561): success; artifact `13070002412`; `PASS_CANDIDATE`, 681 source files hashed, complete hash inventory, 1,206 JUnit cases / 0 failures / 0 errors / 18 skipped.
- Production PostgreSQL Gate [41272250520](https://github.com/butnee-sys/gerchain/actions/runs/41272250520): success; artifact `13069168501`; `PASS_CANDIDATE`, source hashes complete, all 17 migrations applied, matching SQL/database SHA-256 checksums, lifecycle JUnit 6/6.
- core-gates [41272250545](https://github.com/butnee-sys/gerchain/actions/runs/41272250545): success; core contract 56/56 and deep reconciliation 24/24.
- SHUUD/SANDBOX Product MVP [41272250554](https://github.com/butnee-sys/gerchain/actions/runs/41272250554): success; product JUnit 108 cases / 0 failures / 0 errors / 1 skipped.
- Independent Production Audit [41272250536](https://github.com/butnee-sys/gerchain/actions/runs/41272250536): success; audit verdict explicitly says automated evidence, not production-ready certification.
- EAI PostgreSQL Re-performance [41272250524](https://github.com/butnee-sys/gerchain/actions/runs/41272250524), PostgreSQL Production Re-performance [41272250570](https://github.com/butnee-sys/gerchain/actions/runs/41272250570), and FINAL EAI/CORE Exact-SHA Gate [41272250607](https://github.com/butnee-sys/gerchain/actions/runs/41272250607): success; run artifacts bind to `c0086ba...`.

### Failure and skip disposition

- The 21 historical failures are all passing at test level on this checkpoint: 20 SHUUD product cases pass in the isolated product JUnit; the old workflow-isolation test is superseded by and replaced with a passing manual-entrypoint contract test in Production Gate JUnit. The row-by-row mapping is in `docs/FINAL_LOCK_21_FAILURE_DISPOSITION_REGISTER.md`.
- The PostgreSQL process-restart test `test_shuud_survives_postgres_process_restart` remains skipped because `SHUUD_POSTGRES_DSN` was not configured. A workflow-only change in commit `0024117681c2bc004ed24e548f5526f3e8ab333e` now supplies that variable; it has not yet been executed on the post-change candidate.
- Broad EAI regression JUnit reports 1,212 cases / 0 failures / 0 errors / 18 skipped. Those environment-gated tests are not relabelled as passed. Dedicated gates cover some PostgreSQL functions, but DEE PostgreSQL concurrent rotation remains unverified by this broad job.
- PostgreSQL production re-performance evidence is SHA-consistent and `PASS_CANDIDATE`; however its reconciliation report is an empty-baseline check with zero value-flow rows, not a populated production transaction graph.

### Remaining Master Gate controls

MG-07 legacy authority-store physical write freeze; MG-08 IAM/MFA and privileged access; MG-09 observability, alerting, restart/recovery and no-duplicate movement; MG-10 production-like performance/concurrency; MG-11 backup/restore/DR and post-restore reconciliation; MG-12 protected release/branch governance; MG-13 independent attributed re-performance acceptance; and MG-14 complete evidence index plus explicit authorized final approval remain OPEN or require review. The independent audit workflow success is not a signed independent approval of all these controls.

The plan and failure-register updates, plus the PostgreSQL restart workflow configuration, create a new candidate SHA. The `c0086ba...` artifacts are evidence only for that checkpoint. All mandatory gates, source hashes, JUnit, PostgreSQL restart and independent re-performance must be rerun/reconciled against the final post-documentation SHA.

**MASTER GATE = OPEN; PRODUCTION READY = NOT VERIFIED; FINAL LOCK = OPEN.**


## Exact-SHA evidence audit — 2026-11-01 — candidate `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`

This addendum supersedes prior candidate snapshots for the current branch evidence only. It does not close the Master Gate or grant production readiness. The full run/artifact review and MG-07–MG-14 assessment is retained in [the 2026-11-01 evidence audit](evidence/PRODUCTION_FINAL_LOCK_AUDIT_2026-11-01_8850c64.md).

Same-SHA completed workflows include Production Gate run 41283229336 (`PASS_CANDIDATE`, 313 JUnit suites, 0 failures/errors, 18 skipped), Production PostgreSQL Gate run 41283229283 (`PASS_CANDIDATE`, 17 migrations, 13 source hashes complete, lifecycle JUnit 6/6), core-gates run 41283229268 (56/56 core and 24/24 deep reconciliation), SHUUD/SANDBOX Product MVP run 41283229307 (108/108), EAI PostgreSQL Re-performance run 41283229290, PostgreSQL Production Re-performance run 41283229289, and Independent Production Audit run 41283229297. Each run's head SHA is `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`.

Independent SHA-256 recomputation from the GitHub contents at this SHA matched all 17 migration hashes and all 13 source hashes in the PostgreSQL lifecycle report. The broad EAI regression JUnit still has 18 environment-gated skips; these are not relabelled PASS. PostgreSQL production reconciliation is an empty-baseline report, not a populated transaction graph.

MG-07 physical legacy-store freeze, MG-08 independently verified IAM/MFA and privileged access, MG-09 operational observability/alerting/recovery, MG-10 production-like performance/load, MG-11 PostgreSQL backup/restore/DR, MG-12 branch/ruleset governance, MG-13 signed independent re-performance, and MG-14 complete evidence index/authorized approval remain OPEN or PARTIAL. See the audit addendum for itemized reasons.

**MASTER GATE = OPEN; PRODUCTION READY = NOT VERIFIED; FINAL LOCK = OPEN.**
