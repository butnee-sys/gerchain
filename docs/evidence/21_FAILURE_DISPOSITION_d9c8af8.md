# 21-failure disposition register — baseline d9c8af8

**Baseline commit:** `d9c8af8d7b9498ff6c814543112a06d11f73602b`  
**Source run:** Production PostgreSQL Gate `39849400091`, artifact `12456921635`, `segmented-tests/root-tests.log`  
**Observed result:** 21 failed, 899 passed, 50 skipped (root regression segment).  
**Disposition status:** OPEN — none of the 21 failures is recorded as fixed or waived. This register records observed evidence and the next required decision; it does not convert failures into passes.

## Failure-by-failure register

| # | Test | Observed cause in log | Requirement / scope | Required correction or justified disposition | Status |
|---:|---|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Assertion expected a `paths:` filter; workflow currently uses `workflow_dispatch` and the checked workflow body does not satisfy that contract. | CI isolation / SHUUD workflow boundary; not an EAI PostgreSQL acceptance test. | Decide whether path isolation is mandatory. If yes, implement correct trigger/filter and test; otherwise revise the contract test with documented workflow intent. | OPEN |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time`. | SHUUD lifecycle timestamp ordering. | Fix test clock/data ordering or lifecycle transition logic; prove monotonic timestamps in a deterministic test. | OPEN |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error. | SHUUD incident-to-escrow lifecycle. | Trace supplied milestone timestamps and correct fixture or transition order; rerun the end-to-end path. | OPEN |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'`. | SHUUD API response/persistence contract. | Establish expected response schema and restore/persist incident identifier; verify restart recovery. | OPEN |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | `AttributeError: '_IncludedRouter' object has no attribute 'path'`. | SHUUD FastAPI route inspection / app composition. | Update route inspection for installed FastAPI router representation or adjust app composition; preserve route coverage. | OPEN |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` attribute error. | SHUUD route ordering / static mount. | Inspect supported router representation and assert route ordering without relying on absent attribute. | OPEN |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path`. | DEE release-path security boundary. | Identify the unprotected path, add approved protection or document and exclude only if outside release scope; security test must pass closed. | OPEN |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt`. | SHUUD economic impact input validation. | Align validation tests/API signature; ensure incomplete inputs fail with intended domain validation, not Python argument-binding error. | OPEN |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing keyword-only arguments. | Same as #8. | Same correction; retain individual invalid-input assertion. | OPEN |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing keyword-only arguments. | Same as #8. | Same correction; retain individual invalid-input assertion. | OPEN |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt`. | Same as #8. | Same correction; prove the intended error contract for this input. | OPEN |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles`. | Same as #8. | Same correction; prove the intended error contract for this input. | OPEN |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one canonical snapshot; observed zero. | SHUUD KPI snapshot persistence/aggregation. | Trace canonical snapshot write/read path and fixture setup; verify exactly-once counting. | OPEN |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one snapshot; observed zero. | SHUUD economic measurement replacement/idempotency. | Repair snapshot association or test fixture; prove replacement does not double-count. | OPEN |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error. | SHUUD measurement API timing/economics summary. | Correct time fixture/transition ordering; verify summary fields after valid lifecycle. | OPEN |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error. | SHUUD measurement summary composition. | Same timestamp diagnosis as #2; rerun with monotonic milestones. | OPEN |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error. | SHUUD timing-only measurement. | Ensure timing-only path uses valid monotonic event times and does not require economic assumptions. | OPEN |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected regex did not match actual validation error. | SHUUD economic input validation contract. | Define canonical error type/message for incomplete economics; update implementation or assertion based on intended public contract. | OPEN |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error. | SHUUD operational timing invariants. | Correct event order/clock fixture or lifecycle implementation; assert nonnegative durations. | OPEN |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 for expected route. | SHUUD process restart / route availability. | Confirm intended route and mount path; correct routing or test URL, then verify persistence across a real restart. | OPEN |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status`. | SHUUD sandbox configuration validation. | Supply or default status according to config contract; ensure invalid windows/thresholds are rejected for the right reason. | OPEN |

## Evidence and boundaries

- The 21 failures above are from the **root regression segment**, not the PostgreSQL-only diagnostic segments. They are not to be conflated with DB tests that were deliberately run after unsetting database environment variables.
- The canonical architecture tests in the separate core gate passed 56/56 on this SHA. Their report explicitly asserts SHUUD is not part of the Core acceptance manifest. This supports treating SHUUD as a separate application boundary, but does **not** erase failures from a repository-wide test suite or waive a release policy that requires the entire suite to pass.
- The PostgreSQL lifecycle artifact `12456921635` records `evidence_status=PASS_CANDIDATE`, `commit_sha=checked_out_head_sha=d9c8af8...`, 17 migration files, matching migration checksums, valid checksum manifest, and JUnit 6 tests / 0 failures / 0 errors / 0 skipped. This is scoped migration-lifecycle evidence only; it is not proof that the 21 root failures are resolved.
- PostgreSQL Production Re-performance artifact `12457545216` is **SHA-mismatched**: `github_sha` and `checked_out_sha` are `e872ba14c40be0904260308e626aaab8d0a4c6f7`, while the intended candidate is `d9c8af8d7b9498ff6c814543112a06d11f73602b`. Do not attribute this artifact to the candidate SHA.
- The EAI PostgreSQL Re-performance artifact `12456442917` has `commit.txt` and `final-commit.txt` equal to `d9c8af8...`; its JUnit/report data is separate evidence and must be evaluated on its own scope.
- No failure is marked fixed, accepted, or waived here. Each row requires a linked correcting commit and passing rerun, or a documented scope/requirement decision approved by the responsible reviewer.

## Lock decision

`FINAL LOCK = OPEN`  
`PRODUCTION READY = NOT VERIFIED`

Do not close the lock until all required corrections/dispositions, exact-SHA evidence, independent re-performance, production controls, recovery/DR, security/IAM, observability, performance, release governance, and authorized approval are linked to one identical candidate commit.
