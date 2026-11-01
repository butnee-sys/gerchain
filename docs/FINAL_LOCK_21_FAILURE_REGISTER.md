# FINAL LOCK — 21 Failure Disposition Register

**Status:** OPEN — no failure is marked fixed or waived by this register.  
**Source diagnostic:** Production PostgreSQL Gate run `39849400091`, artifact `12456362962` (segmented diagnostics), commit recorded in related evidence: `d9c8af8d7b9498ff6c814543112a06d11f73602b`.  
**Scope note:** All 21 root-suite failures below are SHUUD-related. The canonical EAI/CORE acceptance manifest separately asserts that SHUUD is not part of core acceptance. That architectural boundary does not by itself waive failures from the repository-wide regression suite; each item needs an explicit scope decision or a fix and rerun.

| # | Failing test | Observed cause in log | Requirement / disposition evidence needed | Status |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Test expected workflow `paths:`; actual workflow is `workflow_dispatch` and sandbox-smoke job is disabled. | Confirm intended workflow isolation contract; update test or workflow only with reviewed scope rationale. | OPEN |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time`. | Verify fixture/event chronology and lifecycle timestamp invariant; rerun. | OPEN |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error. | Verify API event ordering and timestamp source; rerun. | OPEN |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'`. | Verify persistence/recovery response contract and stored incident identity; rerun. | OPEN |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | Starlette `_IncludedRouter` has no `.path` attribute. | Align route introspection test with supported FastAPI/Starlette routing API; rerun on pinned dependencies. | OPEN |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` assumption. | Same routing API/dependency compatibility evidence; rerun. | OPEN |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | SecurityError: release contains an unprotected DEE path. | Identify missing protected path and prove policy/manifest coverage; do not weaken fail-closed check. | OPEN |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt`. | Reconcile test input contract with economic measurement API; rerun. | OPEN |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing keyword-only arguments. | Same API/validation contract evidence; rerun. | OPEN |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing keyword-only arguments. | Same API/validation contract evidence; rerun. | OPEN |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt`. | Same API/validation contract evidence; rerun. | OPEN |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles`. | Same API/validation contract evidence; rerun. | OPEN |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one snapshot; observed zero. | Verify snapshot persistence, query/filter and aggregation contract; rerun. | OPEN |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one canonical snapshot; observed zero. | Verify update/replacement and deduplication semantics; rerun. | OPEN |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error. | Verify measurement API chronology and source timestamps; rerun. | OPEN |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error. | Verify summary fixture and chronological invariant; rerun. | OPEN |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error. | Verify timing-only path does not depend on economic assumptions and preserves chronology; rerun. | OPEN |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected validation message regex did not match. | Confirm required-input validation contract and stable error response; rerun. | OPEN |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error. | Verify lifecycle milestone ordering and duration calculation; rerun. | OPEN |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 after restart. | Verify restart route registration, persisted state and API route; rerun against real process. | OPEN |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status`. | Reconcile configuration constructor/defaults with validation contract; rerun. | OPEN |

## Evidence and SHA reconciliation

- The diagnostic artifact is historical evidence from `d9c8af8...`; it is not proof of the same outcomes on a later commit.
- The EAI PostgreSQL re-performance artifact `12456442917` records `d9c8af8...`, with Core JUnit 56/56 and deep-reconciliation JUnit 24/24 passing.
- The PostgreSQL Production Re-performance artifact `13024285607` records `e872ba14c40be0904260308e626aaab8d0a4c6f7` in both `github_sha` and `checked_out_sha`, while the associated run's previously observed head SHA was `d9c8af8...`. This is a material SHA discrepancy and must be resolved against the exact workflow run attempt before the artifact is accepted as evidence for either candidate.
- That PostgreSQL artifact reports 17/17 migration files and applied history checksums matching, lifecycle JUnit 6 tests with 0 failures/errors/skips, PostgreSQL 16.15, and production boot PASS. Its reconciliation is explicitly an empty-baseline reconciliation.
- The segmented regression diagnostic for `d9c8af8...` reports 21 root failures / 899 passes / 50 skips. Additional segmented groups failed because PostgreSQL environment variables were deliberately unset; those are separate diagnostic-environment failures and must not be conflated with the 21 SHUUD root failures.
- A separate exact-SHA artifact, run `39849400071`, and independent audit run `39849399908` succeeded on the previously reported `d9c8af8...`; they do not resolve the later `e872ba14...` artifact discrepancy or the 21 SHUUD failures.

## Acceptance rule

Do not mark any row resolved without (1) a fix commit or approved, explicit out-of-scope disposition, (2) a rerun on the candidate SHA, (3) retained test/JUnit evidence, and (4) a SHA-bound independent review where applicable. Keep `FINAL LOCK = OPEN` and `PRODUCTION READY = NOT VERIFIED` until all production gates and authorized sign-off are evidenced on one identical commit.
