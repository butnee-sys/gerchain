# FINAL LOCK — 7-Step Cumulative Progress Register

**Scope:** Fundamental Architecture + EAI (Escrow as Infrastructure). CORE is one infrastructure/sub-infrastructure, not the whole scope. Product layers including SHUUD/SHIID remain excluded until EAI is production-ready and locked.

**Rule:** Work completed must accumulate as evidence. “0” is not a valid summary when implementation artifacts, tests, boundary corrections, migration checks, or audit records have been produced. However, implementation is not the same as verified production readiness. Every result is counted in the correct evidence class.

## Progress model

- **Implemented:** a code/document change exists at a known repository revision.
- **Tested:** a named test exists or has been run; distinguish test code from an actual test result.
- **Verified:** a fresh, reproducible result exists for the exact commit and environment.
- **Locked:** required evidence has been reviewed, blockers closed, and the gate explicitly accepted.

No status may be promoted from implemented to tested, verified, or locked without new evidence.

## The seven gates

| # | Gate | Current status | Accumulated result | Remaining closure condition |
|---|---|---|---|---|
| 1 | Architecture Reconciliation | **SUBSTANTIALLY IMPLEMENTED / NOT LOCKED** | Canonical architecture freeze exists; value-authority map and legacy-authority freeze exist; canonical-vs-legacy boundaries and adapter requirements are documented. | Reconcile all evidence documents to one exact baseline SHA; independently confirm no contradictory authority paths remain. |
| 2 | Capability Reconciliation | **IN PROGRESS / NOT LOCKED** | Canonical runtime cutovers have been implemented for account creation/read, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT and escrow-state READ; deep value-truth reconciliation and operation/evidence binding checks have been added; production factory now invokes canonical PostgreSQL runtime and checks the versioned migration chain/schema invariants. | Run exact-SHA tests; prove migrations 001–017 apply on a clean PostgreSQL database; exercise the full operation matrix; verify reconciliation results and restart/recovery. |
| 3 | CORE Assurance | **PARTIAL EVIDENCE / NOT LOCKED** | Prior CORE technical controls and frozen evidence records exist. | Reconcile stale baseline references, collect exact-SHA CI evidence, close IAM/MFA and branch-governance evidence gaps, obtain independent re-performance. |
| 4 | Transaction Assurance | **IMPLEMENTED PATHS / NOT VERIFIED END-TO-END** | Transaction-aware Ledger mutation, durable escrow transitions, idempotency, witness, integrity hash and outbox are wired into canonical operation paths. | Real PostgreSQL atomic commit/rollback, replay/conflict, concurrency and exactly-once value-movement tests on the target revision. |
| 5 | Recovery & Audit | **PARTIAL / NOT LOCKED** | Deep cross-store reconciliation checks movement-to-escrow/witness/outbox/idempotency relationships and integrity binding; state-only LOCK is distinguished from value movement. | Run on PostgreSQL; prove abandoned-processing recovery, no duplicate movement after restart, complete evidence graph, and retained audit outputs. |
| 6 | Security & Operations | **PARTIAL / NOT LOCKED** | Production entrypoint rejects non-PostgreSQL configuration, uses canonical runtime construction, and schema bootstrap validates migration history, required columns, uniqueness and critical CHECK constraints. | Production deployment boot, health/readiness, secrets/IAM/MFA, privileged-access review, observability, load/DR and operational runbook evidence. |
| 7 | Final Lock | **NOT STARTED — BLOCKED BY GATES 1–6** | This register creates the cumulative accounting mechanism; it does not declare a production lock. | All required evidence attached to one immutable revision; all blockers closed or formally accepted; independent re-performance and explicit lock approval. |

## Current cumulative position

- **Step 1:** material architecture and authority artifacts exist; baseline reconciliation remains open.
- **Step 2:** active. Multiple implementation and control artifacts exist, so the implementation-result count is **not zero**. Production verification is still unproven until exact-SHA tests and clean PostgreSQL execution produce retained results.
- **Steps 3–6:** have existing partial evidence and explicit open controls; not yet closed.
- **Step 7:** cannot be marked complete before the earlier gates close.

This register deliberately does **not** invent a percentage. Progress is reported by gate and evidence class so that implemented work is counted without disguising unverified production behavior as success.

## Current next action — Step 2 evidence gate

1. Pin the exact branch commit SHA.
2. Run the repository test suite and capture the result against that SHA.
3. Apply the complete versioned migration chain to a fresh PostgreSQL database.
4. Boot the production entrypoint using that same database.
5. Exercise CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ.
6. Run deep value-truth reconciliation and preserve its complete report.
7. Restart the runtime and re-check balances, movement count, witness, outbox and idempotency for duplicate or missing effects.

**No green claim until those results are actually returned. No production lock until independent re-performance.**

## Exact-SHA failure disposition register — candidate `a8fd6092ace34dcd63a763f505af9be93d549574`

**Evidence reviewed:** PostgreSQL Production Gate run [40046489334](https://github.com/butnee-sys/gerchain/actions/runs/40046489334), artifact [12541582297](https://github.com/butnee-sys/gerchain/actions/runs/40046489334/artifacts/12541582297); segmented diagnostic artifact [12541189019](https://github.com/butnee-sys/gerchain/actions/runs/40046489334/artifacts/12541189019); independent EAI audit run [40046489318](https://github.com/butnee-sys/gerchain/actions/runs/40046489318).

The production PostgreSQL JSON report is valid on this candidate and its detached SHA-256 file matches the report bytes. The report records `PASS_CANDIDATE`, matching `commit_sha` / `checked_out_head_sha`, all 13 listed source files hashed, no missing source paths, all 17 migration files matched to the 17 applied migration checksums, exact migration history, and lifecycle JUnit with 6 tests / 0 failures / 0 errors / 0 skipped. This is limited PostgreSQL lifecycle evidence, not final production certification.

The broad diagnostic currently reports **20 failed, 900 passed, 50 skipped**. The previous workflow-isolation failure is no longer in the failure list. The 20 remaining failures below are all in the separate SHUUD/SANDBOX product test surface. The EAI production audit explicitly excludes SHUUD/SANDBOX, and the Master Gate defines SHUUD as a separate, out-of-scope application. This is a scope disposition for the EAI gate only; it is **not** a claim that the SHUUD failures are fixed or that its own release is ready. Root causes and same-SHA targeted re-performance remain open for the SHUUD workstream.

| # | Failing test | Observed failure | Requirement / scope mapping | Current disposition | Closure evidence still required |
|---:|---|---|---|---|---|
| 1 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time` | SHUUD lifecycle timing; separate app, outside EAI gate | Not waived; SHUUD backlog | Identify which supplied milestone ordering is invalid; correct code or fixture; targeted rerun |
| 2 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error | SHUUD HTTP-to-escrow lifecycle | Not waived; SHUUD backlog | Trace timestamp ordering through HTTP flow; targeted rerun |
| 3 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'` | SHUUD persistence/recovery API contract | Not waived; SHUUD backlog | Verify persisted response/schema contract and restart recovery; targeted rerun |
| 4 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | `AttributeError: '_IncludedRouter' object has no attribute 'path'` | SHUUD route-registration test | Not waived; SHUUD backlog | Update route inspection to supported framework API or correct router setup; targeted rerun |
| 5 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` attribute error | SHUUD route ordering | Not waived; SHUUD backlog | Verify route order using supported router representation; targeted rerun |
| 6 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path` | SHUUD DEE release-path protection | Not waived; SHUUD backlog | Identify unprotected path and enforce protection or update a demonstrably stale fixture; security test must pass |
| 7 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` arguments | SHUUD economics input validation | Not waived; SHUUD backlog | Align validation API and test input contract; targeted rerun |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing required arguments | SHUUD economics input validation | Not waived; SHUUD backlog | Same as row 7; demonstrate intended invalid-input behavior |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing required arguments | SHUUD economics input validation | Not waived; SHUUD backlog | Same as row 7; targeted rerun |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt` | SHUUD economics input validation | Not waived; SHUUD backlog | Align signature and test case; targeted rerun |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles` | SHUUD economics input validation | Not waived; SHUUD backlog | Align signature and test case; targeted rerun |
| 12 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected count 1, observed 0 | SHUUD KPI persistence/aggregation | Not waived; SHUUD backlog | Trace snapshot persistence and aggregation query; targeted rerun |
| 13 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected count 1, observed 0 | SHUUD KPI update/no-double-count | Not waived; SHUUD backlog | Trace update identity and aggregation; targeted rerun |
| 14 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error | SHUUD measurement API | Not waived; SHUUD backlog | Correct milestone ordering/validation contract; targeted rerun |
| 15 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error | SHUUD measurement summary | Not waived; SHUUD backlog | Trace timestamps supplied to summary; targeted rerun |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error | SHUUD timing-only measurement | Not waived; SHUUD backlog | Separate timing validation from optional economics assumptions where required; targeted rerun |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected “must be supplied together”; got backward-time error first | SHUUD economics validation order | Not waived; SHUUD backlog | Make validation ordering deterministic and assert the intended incomplete-input error; targeted rerun |
| 18 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error | SHUUD operational timing invariants | Not waived; SHUUD backlog | Verify event chronology and duration calculation; targeted rerun |
| 19 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 for expected route | SHUUD process-restart endpoint | Not waived; SHUUD backlog | Confirm mounted route and restart test configuration; targeted rerun |
| 20 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status` | SHUUD sandbox configuration validation | Not waived; SHUUD backlog | Align configuration constructor/defaults and invalid-config test; targeted rerun |

**EAI release decision:** these failures do not by themselves change the explicitly frozen EAI scope, but they must not be represented as resolved. Keep the broad diagnostic result visible and retain the EAI-specific audit boundary. Any change to the scope boundary requires an explicit architecture decision and new tests.

**Still blocking FINAL LOCK:** the `core-gates` workflow has not produced a completed passing run on this candidate; current automated PostgreSQL evidence is bounded; IAM/MFA and privileged-access proof, legacy authority-store write-freeze proof, observability/recovery/no-duplicate-movement, production-like performance/concurrency, backup/restore/DR, release governance, complete evidence index, independent re-performance at the final immutable SHA, and authorized final approval remain open.

**Disposition remains: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.**



## Exact-SHA disposition and MG-07–MG-14 checkpoint — 2026-11-01 — candidate `ebfa794fa02d7027614b63ad274f85bbd79599c5`

This checkpoint records evidence collected from retained GitHub Actions artifacts for the exact candidate SHA above. It does not grant production readiness or final lock.

### 1. Previous 21 regression failures — exact test disposition

The earlier segmented diagnostic at `d9c8af8d7b9498ff6c814543112a06d11f73602b` recorded 21 failures. Those failures are now reconciled against fresh evidence on candidate `ebfa794fa02d7027614b63ad274f85bbd79599c5`.

**Disposition rule:** `FIXED` means the exact previously failing test was rerun and passed on this candidate. It does not mean that a separate product has received production certification. `OUT OF SCOPE` is not used to hide a failed test.

| # | Exact previously failing test | Previous cause | Current disposition | Same-candidate evidence |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Workflow contract expected a `paths:` filter while the SHUUD workflow was `workflow_dispatch`-only | **FIXED** | Production Gate run 41229008898, artifact 13052613044; `tests__test_final_lock_contract.py.junit.xml`: 5 tests, 0 failures, 0 errors |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | Backward operational milestone timestamp rejected | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Backward operational milestone timestamp rejected | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | Missing `incident_id` in persisted API response | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | Test assumed `_IncludedRouter.path` exists | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Test assumed `_IncludedRouter.path` exists | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | Unprotected DEE release path detected | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Required economic input arguments missing | **FIXED** | Product run 41229008774, artifact 13052483916; exact parametrized case passed |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Required economic input arguments missing | **FIXED** | Product run 41229008774, artifact 13052483916; exact parametrized case passed |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Required economic input arguments missing | **FIXED** | Product run 41229008774, artifact 13052483916; exact parametrized case passed |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | `vehicle_value_per_minute_mnt` missing | **FIXED** | Product run 41229008774, artifact 13052483916; exact parametrized case passed |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | `affected_vehicles` missing | **FIXED** | Product run 41229008774, artifact 13052483916; exact parametrized case passed |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Persisted KPI aggregate returned zero instead of one | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Updated measurement aggregate returned zero instead of one | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward operational milestone timestamp rejected | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward operational milestone timestamp rejected | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward operational milestone timestamp rejected | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Validation order surfaced timestamp error before incomplete-input error | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward operational milestone timestamp rejected | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | Expected route returned HTTP 404 | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig` required `status` argument | **FIXED** | Product run 41229008774, artifact 13052483916; exact test passed |

Product workflow result on this SHA: **107 passed, 1 skipped**. The skipped case is the separate `tests/test_shuud_process_restart_postgres_e2e.py::test_shuud_survives_postgres_process_restart`; it is not one of the 21 historical failures. It remains an OPEN product-level PostgreSQL restart item and must not be called fixed. The production gate's contract JUnit also passed all 5 tests, including the workflow-isolation contract.

The EAI scope boundary remains unchanged: SHUUD/SANDBOX are separate product MVPs and are not EAI acceptance components. Their product tests are run in a separate workflow. This scope separation is not used as the disposition for the 20 failures: each exact historical test passed in the separate product workflow on this candidate.

### 2. Candidate evidence and SHA reconciliation

Primary candidate PostgreSQL evidence:
- Production PostgreSQL run: [41229008828](https://github.com/butnee-sys/gerchain/actions/runs/41229008828), artifact **13052827184** (`production-postgres-evidence-ebfa794fa02d7027614b63ad274f85bbd79599c5`).
- EAI/CORE exact-SHA run: [41229009018](https://github.com/butnee-sys/gerchain/actions/runs/41229009018), artifact **13052552479**.
- Production Gate run: [41229008898](https://github.com/butnee-sys/gerchain/actions/runs/41229008898), artifact **13052613044**.
- Independent automated EAI audit: [41229008907](https://github.com/butnee-sys/gerchain/actions/runs/41229008907), artifact **13052637303**.
- SHUUD/SANDBOX product workflow: [41229008774](https://github.com/butnee-sys/gerchain/actions/runs/41229008774), artifact **13052483916**.

Verified from artifact 13052827184:
- `commit_sha` = `checked_out_head_sha` = `tested_commit` = `ebfa794fa02d7027614b63ad274f85bbd79599c5`.
- `evidence_status=PASS_CANDIDATE`.
- `source_file_count=13`, `source_hashes_complete=true`, `source_missing=[]`, `source_worktree_clean=true`.
- All 17 migration files are listed and match the 17 applied database migration versions and checksums; versions are exactly 1–17.
- The separate `migration-history.json` contains non-null `applied_at` for all 17 rows.
- Lifecycle JUnit: 6 tests, 0 failures, 0 errors, 0 skipped.
- Detached SHA-256 for `migration-lifecycle-report.json` matches the report bytes: `1420d615fa8c6d1d955e773f08f36e7b41a59b4b1192860a7820492a18df9ade`.

Verified from artifact 13052613044:
- `canonical_commit_sha` = `checked_out_head_sha` = `commit_sha` = candidate SHA.
- `evidence_status=PASS_CANDIDATE`, `gate_file_failure_count=0`.
- The manifest's `github_event_sha` is `bcdc2f7f51c8594a6872b3323e402840027e1f32`, the GitHub PR merge/event SHA, and is intentionally distinct from the checked-out PR head. It is not to be substituted for the candidate SHA. All canonical candidate identity fields above match.
- Production Gate per-file JUnit totals: 1,206 tests, 0 failures, 0 errors, 18 skipped.

Verified from artifact 13052827184 segmented EAI regression:
- 1,212 tests, 0 failures, 0 errors, 18 skipped.
- Scope disposition explicitly records SHUUD/SANDBOX as separate product MVPs and excludes them from EAI acceptance.

Verified from artifact 13052637303:
- Independent audit metadata binds to candidate SHA and PostgreSQL 16.
- Audit verdict says collection and EAI tests succeeded, while explicitly describing the result as automated evidence, not production-ready certification. This is bounded automated audit evidence, not independent final approval.

### 3. MG-07–MG-14 evidence and ownership register

No human evidence owner or authorized approver is inferred. Where the repository has not recorded a named accountable owner, this register states **Owner: not assigned in retained evidence**.

| Gate | Requirement | Evidence at candidate SHA | Owner / verification | Status and remaining closure evidence |
|---|---|---|---|---|
| MG-07 | Legacy authority-store write freeze | Architecture and scope documentation; EAI tests and audit pass | Owner: not assigned; physical read-only/write-denial verification not retained | **OPEN** — prove all production routes cannot write legacy stores; retain negative tests and database privilege evidence |
| MG-08 | Security, IAM/MFA, privileged access | CodeQL success and automated code checks only | Owner: not assigned; no IAM/MFA or privileged-access review attached | **OPEN** — current identity-provider policy export, MFA enforcement, privileged account inventory and review approval |
| MG-09 | Observability and operational recovery | Lifecycle/reperformance tests provide bounded restart and consistency evidence | Owner: not assigned; no production monitoring/alert or no-duplicate movement operational drill attached | **OPEN** — health/readiness, alerting, restart/recovery, abandoned-processing recovery and duplicate-movement proof |
| MG-10 | Production-like performance and concurrency | PostgreSQL concurrency/migration tests passed in CI; no production-like workload report attached | Owner: not assigned; CI test is not a load-test acceptance report | **OPEN** — reproducible load profile, concurrency/latency/error measurements and accepted thresholds |
| MG-11 | Backup, restore and disaster recovery | No retained restore/DR drill artifact identified | Owner: not assigned | **OPEN** — backup integrity, restore drill, post-restore reconciliation and documented RPO/RTO evidence |
| MG-12 | CI/release governance | Exact-SHA workflows and CI checks passed on candidate | Owner: repository/release authority not formally named; protected-branch and release approval evidence not retained | **UNVERIFIED** — attach branch protection/ruleset export, required checks, release signing/approval and deployment-to-SHA binding |
| MG-13 | Independent re-performance | Automated audit run 41229008907 and PostgreSQL re-performance runs passed on candidate | Audit is automated and bounded; independent human reviewer/sign-off not recorded | **OPEN** — independent reviewer re-run, retained method/results, findings and signed acceptance on immutable final SHA |
| MG-14 | Evidence index and authorized final approval | This checkpoint maps the retained artifacts to the candidate SHA | Authorized approver not identified; no final decision record | **OPEN** — complete evidence index, all MG-07–MG-13 closures, named authorized approver and explicit final decision |

### 4. Candidate decision

This checkpoint improves the evidence state but does not close MG-07–MG-14. In particular, the automated audit is not an authorized final approval; CI success is not a substitute for IAM/MFA, operational monitoring, load, backup/restore, and deployment governance evidence.

**MASTER GATE = OPEN. PRODUCTION READY = NOT VERIFIED. FINAL LOCK = OPEN.**

This register commit itself creates a new repository revision. All mandatory workflows must be rerun against the resulting exact commit SHA before that revision can be considered the final candidate. No evidence from a different SHA may be silently carried forward as exact-SHA proof.
