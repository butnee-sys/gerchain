# Production Final-Lock Exception and Failure Register

**Status:** OPEN — FINAL LOCK NOT GRANTED  
**Production status:** NOT VERIFIED  
**Register baseline:** historical diagnostic run 39849400091 at commit `d9c8af8d7b9498ff6c814543112a06d11f73602b`; this is not asserted to be the current PR head.  
**Current PR head at register creation:** `9b75127bd2f09c8524c5335760dea940b3d8aa99`.

## Evidence disposition

| Evidence | Run / artifact | Commit recorded | Result | Disposition |
|---|---|---|---|---|
| PostgreSQL lifecycle | Run 39849400091 / artifact 12456921635 | d9c8af8d7b9498ff6c814543112a06d11f73602b | `PASS_CANDIDATE`; 17/17 migrations; migration checksums match; source hashes complete 13/13; JUnit 6 passed, 0 failed/errors/skipped | Candidate evidence only; not full production certification |
| Exact-SHA registry | Run 39849400071 / artifact 12456762135 | d9c8af8d7b9498ff6c814543112a06d11f73602b | Workflow success; migration manifest records d9c8af8d7b9498ff6c814543112a06d11f73602b | Verify full archive checksums and bind to final candidate |
| EAI PostgreSQL re-performance | Run 39849399950 / artifact 12456442917 | d9c8af8d7b9498ff6c814543112a06d11f73602b | Workflow success | Retain detailed JUnit/logs and independent review |
| PostgreSQL production re-performance | Run 39849400050 / artifact 12457545216 | **e872ba14c40be0904260308e626aaab8d0a4c6f7** | Workflow run was reported against d9c8af8..., but artifact says e872ba... | **SHA MISMATCH — reject as evidence for d9c8af8**; regenerate artifact from exact candidate SHA |
| Independent production audit | Run 39849399908 / artifact 12457226020 | d9c8af8d7b9498ff6c814543112a06d11f73602b | Automated audit says not production certification | Supporting evidence only; independent human/organizational sign-off remains open |
| Production Gate | Run 39849399966, attempt 17 | d9c8af8d7b9498ff6c814543112a06d11f73602b | Cancelled; evidence report `BLOCKED`; migration-history.json and postgres-constraints.json missing; master manifest records stale SHA 5e5193511b47f0815f28a2c6c76fb9f60634b695 | **FAIL-CLOSED**; rerun and repair manifest binding |
| core-gates | Run 39849400130 | d9c8af8d7b9498ff6c814543112a06d11f73602b | Cancelled during full repository test; migration audit skipped | Not a passing full-suite result |

## Prior 21 failing tests — itemized disposition

The following 21 failures were recorded in the segmented root-suite log for the d9c8af8 diagnostic run. Their exact test names and observed failure reasons are retained below. The log did not provide accountable owners, repair commits, post-fix rerun IDs, per-test JUnit proof, or reviewer decisions. Those fields are explicitly unassigned/pending; no ownership or resolution is fabricated.

| # | Test | Observed reason | Requirement / scope | Owner | Fix commit | Rerun + JUnit | Reviewer decision |
|---:|---|---|---|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Test expects workflow `paths:`; workflow uses `workflow_dispatch` | SHUUD workflow isolation; separate app, not canonical EAI prerequisite | Unassigned | Pending | Pending | Pending scope decision |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | Operational milestones rejected as moving backward in time | SHUUD lifecycle timing | Unassigned | Pending | Pending | Pending |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Operational milestones rejected as moving backward in time | SHUUD incident-to-escrow flow | Unassigned | Pending | Pending | Pending |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: incident_id` | SHUUD persistence/recovery API contract | Unassigned | Pending | Pending | Pending |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | FastAPI `_IncludedRouter` has no `path` attribute | SHUUD route registration/introspection | Unassigned | Pending | Pending | Pending |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | FastAPI `_IncludedRouter` has no `path` attribute | SHUUD route ordering | Unassigned | Pending | Pending | Pending |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | DEE security error: release contains an unprotected DEE path | SHUUD/DEE security boundary | Unassigned | Pending | Pending | Pending |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | SHUUD economics input validation | Unassigned | Pending | Pending | Pending |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | SHUUD economics input validation | Unassigned | Pending | Pending | Pending |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | SHUUD economics input validation | Unassigned | Pending | Pending | Pending |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing required `vehicle_value_per_minute_mnt` | SHUUD economics input validation | Unassigned | Pending | Pending | Pending |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing required `affected_vehicles` | SHUUD economics input validation | Unassigned | Pending | Pending | Pending |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one canonical KPI snapshot; observed zero | SHUUD KPI integrity | Unassigned | Pending | Pending | Pending |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one canonical KPI snapshot; observed zero | SHUUD KPI deduplication | Unassigned | Pending | Pending | Pending |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Operational milestones rejected as moving backward in time | SHUUD measurement API | Unassigned | Pending | Pending | Pending |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Operational milestones rejected as moving backward in time | SHUUD measurement summary | Unassigned | Pending | Pending | Pending |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Operational milestones rejected as moving backward in time | SHUUD timing-only measurement | Unassigned | Pending | Pending | Pending |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected “must be supplied together”; received backward-time validation error | SHUUD economics validation ordering | Unassigned | Pending | Pending | Pending |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Operational milestones rejected as moving backward in time | SHUUD operational timing | Unassigned | Pending | Pending | Pending |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 during process-restart flow | SHUUD process restart/recovery | Unassigned | Pending | Pending | Pending |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status` | SHUUD sandbox configuration validation | Unassigned | Pending | Pending | Pending |

## Retest evidence on candidate `94cbb6207bb1fddd4ceaa45a9777d3a02c655857`

Observed 2026-10-31 on the exact candidate SHA `94cbb6207bb1fddd4ceaa45a9777d3a02c655857`:

- Production PostgreSQL Gate run `41225677312`, artifact `13052111408`: PostgreSQL lifecycle JUnit 6/6 passed; segmented EAI regression JUnit 1,212 testcases, 0 failures, 0 errors, 18 skipped; log summary `1,194 passed, 18 skipped`.
- SHUUD and SANDBOX Product MVP Tests run `41225677296`, artifact `13051787915`: JUnit 108 testcases, 0 failures, 0 errors, 1 skipped; log summary `107 passed, 1 skipped`.
- The 20 SHUUD product failures from the historical 21-item list are present and pass in the product JUnit. The historical DEE proof case is `test_shuud_dee_end_to_end_proves_trust_transparency_performance` and passes. The historical workflow-isolation test was replaced by the stronger/current contract `tests/test_final_lock_contract.py::test_shuud_workflows_are_separate_manual_entrypoints`, which passes in the EAI regression JUnit.
- Therefore, all 21 historical failure entries have a passing or superseding test result on candidate `94cbb620...`; this is **not** a formal waiver and does not prove that the entire production gate is green. Retain the historical failure reasons above; the current passing JUnit results are their retest evidence.

### Same-SHA evidence still incomplete on `94cbb620...`

- Production PostgreSQL Gate run `41225677312` failed after the regression and lifecycle test JUnit completed. The evidence-manifest builder raised `NameError: name 'report' is not defined` because `evidence_status` referenced `report["source_worktree_clean"]` while `report` was still being constructed. This is a CI evidence-generation defect; it prevents a valid `PASS_CANDIDATE` report even though the two JUnit suites passed.
- Production Gate run `41225677339` was still in progress at the time of review; core-gates run `41225677301` later ended `cancelled`, with no completed job or artifact. Neither is accepted as a pass.
- PostgreSQL migration/proof artifact `13052041701` binds `commit_sha` and `checked_out_head_sha` to `94cbb620...`, reports a clean worktree, and includes 17 migration SHA-256 entries plus `SHA256SUMS`; scoped logs report 24 deep reconciliation, 6 migration concurrency, 2 rollback, and 1 production runtime boot tests passed.
- Independent audit artifact `13051827699` binds to `94cbb620...` and reports 87 EAI tests passed, but explicitly states it is automated evidence, not production-ready certification.
- Exact-SHA artifact `13051986917` binds to `94cbb620...` and lists all 17 migration SHA-256 values.
- The separate `.github/workflows/postgres-production-reperformance.yml` run `41225672896` failed and exposed no job/artifact through the Actions jobs/artifacts endpoints. Do not infer a pass or treat it as replacement for the previously SHA-mismatched artifact.

### Corrective CI commit

- The self-referential manifest expression was moved to a post-construction calculation in commit `9cf719ccd9812f5b4462d5671340cb5dd2cff0f0` (`fix(ci): avoid self-reference in PostgreSQL evidence manifest`).
- This commit creates a new candidate SHA. All `94cbb620...` evidence is predecessor evidence only and must not be mixed with the new candidate's final evidence. Re-run Production PostgreSQL Gate, Production Gate, core-gates, PostgreSQL proof/re-performance, Exact-SHA, and independent audit on one identical new SHA; verify `tested_commit`, `commit_sha`, and `checked_out_head_sha` equality and the regenerated report's `evidence_status`.
- Do not reuse artifact `12457545216` (embedded SHA `e872ba14...`); it remains quarantined.

**Decision remains:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.

## Required closure fields for every failure

For each row, update only with verifiable evidence:
1. Named accountable owner (or formally approved exclusion owner).
2. Root cause and requirement ID / approved scope classification.
3. Repair commit SHA, or documented reason no code change is required.
4. Exact rerun ID and attempt on the same final candidate SHA.
5. JUnit testcase result (passed/failed/skipped) and log/artifact reference.
6. Reviewer identity, decision, date, and rationale.

A suite-level green status is not a substitute for per-test evidence. SHUUD being outside the canonical EAI dependency chain does not automatically waive these repository-wide failures; any exclusion requires an explicit scope decision and a corresponding gate definition.

## Mandatory open items before final evaluation

- Correct stale `docs/production-master-gate-manifest.json` SHA binding and regenerate it from the exact checkout SHA.
- Rerun Production Gate and core-gates to completion; do not accept cancelled runs.
- Resolve the PostgreSQL Production Re-performance artifact SHA mismatch (e872... versus d9c8...).
- Preserve final full-suite JUnit and resolve all 21 failures individually, or record formally approved scope exclusions with evidence.
- Re-run independent production audit against the same final candidate SHA and obtain reviewer sign-off.
- Supply outstanding IAM/MFA, legacy authority-store write-freeze, observability/recovery, performance/concurrency, backup/restore/DR, release governance, and authorized final-lock decision evidence.

**Decision remains:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.
