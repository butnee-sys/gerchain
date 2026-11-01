# Root-suite 21 Failure Disposition Register

Status: OPEN — no failure is represented as fixed, waived, or accepted.
Evidence baseline: workflow run 39849400091, artifact 12456921635, commit `d9c8af8d7b9498ff6c814543112a06d11f73602b`.
Observed source: `segmented-tests/root-tests.log`. The 21 entries below are the root-suite failures only; separate database-environment and service-segment diagnostics are not included in this count.

## Disposition rules

- A failure is CLOSED only after a corrective commit and a passing rerun on that exact commit, or after a documented scope decision approved by the designated owner and a test proving the EAI boundary is not weakened.
- SHUUD is documented as a separate application and excluded from the EAI canonical acceptance manifest. That boundary does not automatically waive repository-wide regression failures.
- Requirement mapping below is provisional by domain because the artifact does not contain a formal requirement-ID crosswalk. The owner must map each item to the approved requirement/control before closure.
- No code/test changes or waivers are claimed by this register.

## Individual failures

| # | Failing test | Observed cause in log | Provisional requirement area | Disposition / evidence required |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Expected `paths:`; workflow is `workflow_dispatch` and sandbox-smoke is disabled | CI scope isolation / SHUUD workflow governance | OPEN. Decide and document intended trigger/isolation contract; update test or workflow only after owner approval; rerun. |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | Operational milestones rejected as moving backward in time | SHUUD lifecycle chronology | OPEN. Reproduce deterministic clock/order defect; fix implementation or fixture; rerun. |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Operational milestones rejected as moving backward in time | SHUUD incident-to-release lifecycle | OPEN. Reproduce chronology issue and verify end-to-end release; rerun. |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: incident_id` | SHUUD durable incident schema/recovery | OPEN. Trace persisted payload/schema compatibility; add recovery regression evidence; rerun. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | FastAPI `_IncludedRouter` has no `path` attribute | SHUUD route registration / framework compatibility | OPEN. Inspect supported FastAPI route introspection; fix test/app contract; rerun. |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | FastAPI `_IncludedRouter` has no `path` attribute | SHUUD route ordering | OPEN. Verify route order using public API; rerun. |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | Release rejected for an unprotected DEE path | SHUUD DEE release protection | OPEN. Identify unprotected path; prove all release paths are protected; rerun. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | SHUUD economic measurement input validation | OPEN. Align validation API and test fixtures; rerun. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | SHUUD economic measurement input validation | OPEN. Same contract family; retain independent case result; rerun. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | SHUUD economic measurement input validation | OPEN. Same contract family; retain independent case result; rerun. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing required `vehicle_value_per_minute_mnt` | SHUUD economic measurement input validation | OPEN. Same contract family; retain independent case result; rerun. |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing required `affected_vehicles` | SHUUD economic measurement input validation | OPEN. Same contract family; retain independent case result; rerun. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one canonical snapshot; observed zero | SHUUD KPI snapshot integrity | OPEN. Trace snapshot persistence/aggregation; verify no double count; rerun. |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one canonical snapshot; observed zero | SHUUD KPI update/idempotency | OPEN. Trace update/replacement semantics; verify exactly one snapshot; rerun. |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Operational milestones rejected as moving backward in time | SHUUD measurement API chronology | OPEN. Reproduce and correct timestamp ordering; rerun. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Operational milestones rejected as moving backward in time | SHUUD measurement summary chronology | OPEN. Reproduce and correct timestamp ordering; rerun. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Operational milestones rejected as moving backward in time | SHUUD timing-only measurement | OPEN. Separate timing-only path from monetary assumptions; rerun. |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected validation message/pattern did not match | SHUUD economic input validation contract | OPEN. Specify canonical validation error and assert it; rerun. |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Operational milestones rejected as moving backward in time | SHUUD operational timing invariant | OPEN. Reproduce with controlled clock; verify monotonicity and duration calculations; rerun. |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 after process restart | SHUUD restart/API route recovery | OPEN. Trace startup route/state restoration; rerun real-process test. |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__` missing required `status` | SHUUD sandbox configuration validation | OPEN. Align constructor/config schema and validation tests; rerun. |

## Cross-run SHA integrity exception

The PostgreSQL production re-performance artifact (run 39849400050, artifact 12457545216) records `github_sha` and `checked_out_sha` as `e872ba14c40be0904260308e626aaab8d0a4c6f7`, while the GitHub run metadata and its sibling evidence artifacts identify the run head as `d9c8af8d7b9498ff6c814543112a06d11f73602b`. This artifact is therefore not accepted as same-commit evidence. Re-run the workflow and regenerate the artifact; verify run metadata, checkout SHA, manifest SHA, and all migration/source hashes agree before using it.

## Evidence already observed (not a final lock)

- Production PostgreSQL Gate run 39849400091: successful; artifact 12456921635 reports `evidence_status=PASS_CANDIDATE`, `sha_match=true`, `source_hashes_complete=true`, 13 source files, no missing source files, 17 migration files, all migration checksums matching, exact applied migration history, and lifecycle JUnit 6 tests / 0 failures / 0 errors / 0 skipped. This is a candidate report, not final certification.
- FINAL EAI/CORE Exact-SHA Gate run 39849400071: successful; artifact 12456762135 identifies commit d9c8af8... and lists migration versions 001–017. Its `git_status_porcelain` contains modified tracked `__pycache__` files, which must be assessed/cleaned from evidence generation before treating the workspace as clean.
- EAI PostgreSQL Re-performance run 39849399950: successful; artifact 12456442917 identifies d9c8af8... and contains 56/56 core-gates tests and 24/24 deep-reconciliation tests. These scoped suites do not resolve the 21 root-suite failures.
- Independent Production Audit run 39849399908: successful, but its own verdict explicitly says automated evidence is not production-ready certification.
- The two broader runs, Production Gate 39849399966 and core-gates 39849400130, have remained in progress at the latest check. Their jobs were still running the complete test suite; job logs endpoint returned NOT_FOUND. Obtain final JUnit/artifacts after completion.

## Required closure fields

For each row, append: approved requirement/control ID; owner; root-cause analysis; corrective commit SHA or approved scope decision; focused test result; full-suite result; independent reviewer and date. Until every applicable row is closed and the SHA discrepancy is corrected, this register remains OPEN.

Final decision remains: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.
