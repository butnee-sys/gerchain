# EAI diagnostic disposition register — 21 historical root-test failures

**Status:** disposition recorded; not a production-readiness certificate.  
**Observed run:** [Production PostgreSQL Gate #39849400091](https://github.com/butnee-sys/gerchain/actions/runs/39849400091), candidate SHA `d9c8af8d7b9498ff6c814543112a06d11f73602b`.  
**Current candidate at register creation:** `61ec4897d12c97fd4e6b00a9189a529126b0c03b` (workflow-only scope correction; all gates must rerun on the final candidate).  
**Historical root result:** 21 failed, 899 passed, 50 skipped. This is a historical diagnostic, not a statement that the current SHA has the same result.

## Decision rule

The canonical architecture explicitly treats SHUUD/SHIID as separate applications, not EAI prerequisites. Therefore SHUUD application tests must not be represented as passing EAI tests or silently waived for a SHUUD release. They are assigned to the separate SHUUD acceptance workflow. The EAI production gate records the excluded test paths and enforces the canonical EAI suite. No production claim is made for SHUUD based on this disposition.

## Per-test register

| # | Test | Observed cause in historical log | Requirement / boundary | Disposition and evidence |
|---:|---|---|---|---|
| 1 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | Operational milestones rejected as moving backward in time | SHUUD lifecycle/timing | Outside canonical EAI acceptance; unresolved SHUUD defect. Reproduce and fix in SHUUD gate before any SHUUD release. |
| 2 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error | SHUUD incident-to-escrow flow | Outside canonical EAI acceptance; unresolved SHUUD defect. |
| 3 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | Response lacked `incident_id` | SHUUD persistence/recovery contract | Outside canonical EAI acceptance; unresolved SHUUD defect. |
| 4 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | Test inspected `.path` on FastAPI `_IncludedRouter` | SHUUD route-registration contract | Outside canonical EAI acceptance; SHUUD test/app compatibility must be repaired in its own gate. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` assumption | SHUUD route ordering | Outside canonical EAI acceptance; unresolved SHUUD test/app compatibility. |
| 6 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | DEE security rejected an unprotected release path | SHUUD release security | Outside EAI acceptance, but security-significant; must be fixed, not waived, before SHUUD release. |
| 7 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` arguments | SHUUD economics API contract | Outside canonical EAI acceptance; repair test/API contract in SHUUD workstream. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing keyword-only arguments | SHUUD economics API contract | Same disposition as #7. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing keyword-only arguments | SHUUD economics API contract | Same disposition as #7. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt` | SHUUD economics API contract | Same disposition as #7. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles` | SHUUD economics API contract | Same disposition as #7. |
| 12 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one persisted snapshot; observed zero | SHUUD KPI/persistence integrity | Outside canonical EAI acceptance; unresolved SHUUD data-flow defect. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one persisted snapshot; observed zero | SHUUD measurement replacement/idempotency | Outside canonical EAI acceptance; unresolved SHUUD data-flow defect. |
| 14 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Operational milestones rejected as moving backward in time | SHUUD measurement API | Outside canonical EAI acceptance; unresolved SHUUD timing defect. |
| 15 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Operational milestones rejected as moving backward in time | SHUUD measurement summary | Outside canonical EAI acceptance; unresolved SHUUD timing defect. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Operational milestones rejected as moving backward in time | SHUUD timing-only measurement | Outside canonical EAI acceptance; unresolved SHUUD timing defect. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected validation message/pattern did not match | SHUUD input-validation contract | Outside canonical EAI acceptance; align validation behavior and assertion in SHUUD workstream. |
| 18 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Operational milestones rejected as moving backward in time | SHUUD lifecycle timing | Outside canonical EAI acceptance; unresolved SHUUD timing defect. |
| 19 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | Restart endpoint returned HTTP 404 | SHUUD process-restart recovery | Outside canonical EAI acceptance; unresolved SHUUD recovery defect. |
| 20 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig` constructor missing required `status` | SHUUD sandbox configuration contract | Outside canonical EAI acceptance; repair constructor/test contract in SHUUD workstream. |
| 21 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Historical assertion required a `paths:` trigger, while the SHUUD workflow was manual-only | EAI/SHUUD workflow boundary | Historical assertion superseded by `test_shuud_workflows_are_separate_manual_entrypoints`, which checks `workflow_dispatch` and rejects push/PR triggers. **Current-SHA test proof is pending**; do not mark closed until the current run confirms it. |

## Gate changes and verification required

- The EAI diagnostic now records and excludes `tests/test_shuud_*.py` from the root-level EAI diagnostic, matching the canonical boundary; it does not claim these tests passed.
- The excluded list is retained as `artifacts/segmented-tests/shuud-out-of-scope.txt`.
- EAI gate must still pass all in-scope tests, migration/lifecycle checks, exact-SHA/hash checks, and independent re-performance on one final SHA.
- SHUUD remains **not verified for production** until its own manual acceptance workflow fixes and passes the defects above.
- Final lock remains **OPEN** until all remaining production controls (access/IAM, legacy authority write freeze, observability/recovery, performance/concurrency, backup/restore/DR, release governance, independent re-performance, and authorized decision) have retained evidence on the same final SHA.
