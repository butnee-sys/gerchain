# EAI acceptance disposition for the 21 diagnostic failures

**Baseline:** commit `d9c8af8d7b9498ff6c814543112a06d11f73602b`, Production PostgreSQL Gate run [39849400091](https://github.com/butnee-sys/gerchain/actions/runs/39849400091), artifact `segmented-test-diagnostics-e872ba14c40be0904260308e626aaab8d0a4c6f7`.  
**Important:** this is a disposition of the recorded diagnostic failures, not a claim that the SHUUD application passes. SHUUD is explicitly a separate application and outside the GerChain/EAI production acceptance boundary. SHUUD functional acceptance remains unverified until its own workflow is enabled and passes. The EAI acceptance workflows must not fail or pass based on these separate-app tests.

| # | Failing test | Observed failure | Requirement / disposition |
|---:|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Test expected `paths:` filters and path strings, but both workflows are manual `workflow_dispatch` entrypoints. | **Test-contract correction.** Assert manual-only triggers and absence of push/PR triggers instead of requiring path filters. This verifies the actual isolation design. |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time`. | SHUUD lifecycle/timestamp requirement; outside EAI gate. Keep recorded as SHUUD defect until its own acceptance run proves source timestamps are monotonic. |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-milestone timestamp rejection. | SHUUD lifecycle/timestamp requirement; outside EAI gate; unresolved for SHUUD. |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'`. | SHUUD API persistence/recovery contract; outside EAI gate; unresolved for SHUUD. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | FastAPI router introspection expected `.path` on `_IncludedRouter`. | SHUUD route-registration assertion/framework compatibility; outside EAI gate; unresolved for SHUUD. |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` assumption. | SHUUD route-order assertion/framework compatibility; outside EAI gate; unresolved for SHUUD. |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path`. | SHUUD release-path security requirement; outside EAI gate; unresolved and must not be represented as passing. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt`. | SHUUD economics input-validation contract; outside EAI gate; unresolved for SHUUD. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing required keyword-only arguments. | SHUUD economics input-validation contract; outside EAI gate; unresolved for SHUUD. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing required keyword-only arguments. | SHUUD economics input-validation contract; outside EAI gate; unresolved for SHUUD. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt`. | SHUUD economics input-validation contract; outside EAI gate; unresolved for SHUUD. |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles`. | SHUUD economics input-validation contract; outside EAI gate; unresolved for SHUUD. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one snapshot, observed zero. | SHUUD KPI persistence/aggregation contract; outside EAI gate; unresolved for SHUUD. |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected persisted measurement count, observed zero. | SHUUD KPI update/idempotency contract; outside EAI gate; unresolved for SHUUD. |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-milestone timestamp rejection. | SHUUD measurement summary contract; outside EAI gate; unresolved for SHUUD. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-milestone timestamp rejection. | SHUUD measurement summary contract; outside EAI gate; unresolved for SHUUD. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-milestone timestamp rejection. | SHUUD timing-only measurement contract; outside EAI gate; unresolved for SHUUD. |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected paired-input validation message; timestamp validation fired first. | SHUUD input-validation ordering; outside EAI gate; unresolved for SHUUD. |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-milestone timestamp rejection. | SHUUD operational timing contract; outside EAI gate; unresolved for SHUUD. |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 after process restart. | SHUUD process-restart/API recovery contract; outside EAI gate; unresolved for SHUUD. |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig` construction missing required `status`. | SHUUD configuration validation contract; outside EAI gate; unresolved for SHUUD. |

## Acceptance handling

- EAI/core production gates now exclude root-level `tests/test_shuud_*.py` from the EAI acceptance pytest invocation, consistent with `docs/MASTER_GATE_PRODUCTION_FINAL_LOCK.md` and the canonical scope rule that SHUUD is a separate app.
- The SHUUD functional tests are **not marked passed**. Their own acceptance remains **OPEN / NOT VERIFIED**.
- The diagnostic logs remain retained as evidence of these failures; no failure was silenced or rewritten as a pass.
- The JSON report writer was corrected separately because it emitted a literal backslash-n after the JSON object, making the report unparsable. The corrected report must be verified by a fresh exact-SHA run.
- This register does not close IAM/MFA, legacy-store freeze, observability/recovery, performance, backup/restore/DR, release governance, or authorized approval gates.
