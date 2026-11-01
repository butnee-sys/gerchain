# Production Gate Failure Disposition Register

**Status:** OPEN — NOT A PRODUCTION-READINESS CERTIFICATE  
**Reviewed commit:** `d9c8af8d7b9498ff6c814543112a06d11f73602b`  
**Source:** artifact `12456921635`, workflow run [39849400091](https://github.com/butnee-sys/gerchain/actions/runs/39849400091), `segmented-tests/root-tests.log` and `segmented-tests/services.log`.  
**Rule:** Entries below are triage records, not evidence of resolution. No failure is waived without a named requirement, owner-approved scope rationale, and passing re-test on one exact commit.

## Root suite: 21 failures

The recorded root-suite summary is **21 failed, 899 passed, 50 skipped**. The 21 failures are listed individually below.

| # | Failing test | Observed cause from log | Requirement area | Disposition |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Test expects `paths:`; workflow is `workflow_dispatch` and includes a disabled `sandbox-smoke` job. | Workflow isolation / CI contract | OPEN — reconcile test expectation with intended trigger isolation; re-test. |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time`. | Lifecycle timestamp ordering | OPEN — identify source of non-monotonic timestamps; re-test. |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error. | API lifecycle / timestamp ordering | OPEN — trace event timestamps; re-test. |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'`. | API persistence / recovery contract | OPEN — establish response schema and recovery path; re-test. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | `AttributeError: '_IncludedRouter' object has no attribute 'path'`. | Route registration / framework compatibility | OPEN — correct route inspection or app wiring; re-test. |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` assumption. | Route ordering / static mount | OPEN — verify intended route ordering using supported API; re-test. |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path`. | Release path protection / trust evidence | OPEN — identify uncovered path and verify protection; do not weaken security check. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt`. | Economic input validation | OPEN — align validation API and test contract; re-test. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing keyword-only arguments. | Economic input validation | OPEN — align validation API and test contract; re-test. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing keyword-only arguments. | Economic input validation | OPEN — align validation API and test contract; re-test. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt`. | Economic input validation | OPEN — align validation API and test contract; re-test. |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles`. | Economic input validation | OPEN — align validation API and test contract; re-test. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one canonical snapshot; observed count 0. | KPI snapshot integrity | OPEN — trace snapshot persistence/query path; re-test. |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one canonical snapshot; observed count 0. | KPI update / double-count prevention | OPEN — trace update and aggregation semantics; re-test. |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error. | Measurement API / timestamp ordering | OPEN — trace event ordering; re-test. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error. | Measurement summary / timestamp ordering | OPEN — trace event ordering; re-test. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error. | Timing-only measurement | OPEN — validate timing-only path and timestamp source; re-test. |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected validation message regex did not match. | Economic completeness / error contract | OPEN — verify intended validation error and test; re-test. |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error. | Operational timing / lifecycle durations | OPEN — correct timestamp ordering; re-test. |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 Not Found. | Process restart / route availability | OPEN — trace endpoint and restart state; re-test. |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status` argument. | Sandbox configuration validation | OPEN — reconcile constructor and validation contract; re-test. |

## Additional service-suite failures

The same diagnostic artifact also records **6 failed, 56 passed, 2 skipped** under `services.log`. These are separate from the 21 root-suite failures and must not be silently merged into or treated as resolved by the root-suite count:

1. `tests/services/test_canonical_schema_assertion.py::test_canonical_schema_assertion_accepts_complete_schema` — SQLite syntax error near `[0]` while exercising PostgreSQL-oriented schema logic.
2. `tests/services/test_canonical_schema_assertion.py::test_canonical_schema_assertion_rejects_version_marker_with_missing_columns` — expected error text did not match.
3. `tests/services/test_canonical_schema_assertion.py::test_canonical_schema_assertion_rejects_incomplete_migration_history` — SQLite syntax error near `[0]`.
4. `tests/services/test_production_runtime_factory_postgres.py::test_production_runtime_factory_establishes_canonical_authority` — missing `GERCHAIN_TEST_DATABASE_URL`.
5. `tests/services/test_production_schema_constraint_drift.py::test_schema_gate_detects_weakened_constraint_definition` — expected `>=0`, observed `>=`.
6. `tests/services/test_production_self_repair.py::test_repair_rewrites_only_the_approved_legacy_constructor_pattern` — source did not match the approved repair template; no changes written.

## Evidence that is positive, but limited in scope

For run `39849400091`, the archived `production-postgres/migration-lifecycle-report.json` reports `PASS_CANDIDATE`, 17/17 migration checksums matching, exact migration history, `source_hashes_complete=true` with 13 source files and no missing paths, and lifecycle JUnit 6/6 passing. This proves the scoped PostgreSQL lifecycle gate only; it does not close the root/service regression failures or the production operational gates.

## SHA provenance discrepancy — quarantine and regenerate

The run metadata for [PostgreSQL Production Re-performance run 39849400050](https://github.com/butnee-sys/gerchain/actions/runs/39849400050) reports head SHA `d9c8af8d7b9498ff6c814543112a06d11f73602b`, but its downloaded artifacts `migration-catalog-proof.json`, `production-gate-evidence.json`, and `tested-commit.txt` state `e872ba14c40be0904260308e626aaab8d0a4c6f7`. Therefore that artifact is **SHA-MISMATCHED and must not be accepted as evidence for d9c8af8**. Correct workflow/artifact provenance and regenerate on one exact SHA before relying on it.

The separate EAI re-performance artifact `12456442917` records `d9c8af8d7b9498ff6c814543112a06d11f73602b`, and its own `SHA256SUMS.txt` / `SHA256SUMS.sha256` can be checked within that artifact. Do not use its checksum manifest to certify another artifact bundle.

## Still open

At the last check, both [Production Gate run 39849399966](https://github.com/butnee-sys/gerchain/actions/runs/39849399966) and [core-gates run 39849400130](https://github.com/butnee-sys/gerchain/actions/runs/39849400130) remained `in_progress`, with their full repository test-suite step still running. Final logs/JUnit and finalized evidence manifests are not yet available from those runs.

Outstanding operational evidence still includes legacy authority-store write freeze; IAM/MFA and privileged access; observability/recovery/restart/no-duplicate-movement; production-like performance/concurrency; backup/restore/DR drill and reconciliation; release governance and exact candidate SHA; independent re-performance; and authorized final-lock approval.

**Decision remains:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`. No failure is marked resolved, and no final-lock claim is authorized by this register.
