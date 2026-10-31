# SHUUD root-test failure register — 2026-10-22 evidence

**Disposition:** OPEN / NOT RESOLVED. This register records the 21 root-suite failures from the diagnostic artifact produced by Production PostgreSQL Gate run `39849400091` (artifact ID `12456362962`, artifact name `segmented-test-diagnostics-e872ba14c40be0904260308e626aaab8d0a4c6f7`). The run's API metadata reports head `d9c8af8d7b9498ff6c814543112a06d11f73602b`, but the diagnostic artifact is named for `e872ba14c40be0904260308e626aaab8d0a4c6f7`; therefore these failures are historical diagnostics and must not be represented as a fresh exact-SHA result for d9c8af8.

**Observed summary:** `21 failed, 899 passed, 50 skipped` in `root-tests.log`. The Production PostgreSQL Gate itself succeeded because the broad regression diagnostic step has `continue-on-error: true`; this does not mean these 21 tests passed.

**Scope rule:** The Master Gate document explicitly defines SHUUD as a separate, isolated application outside the GerChain/EAI final-lock assurance boundary. That scope distinction may prevent these failures from being treated as GerChain/EAI production-gate failures, but it does not make the SHUUD failures resolved. Each remains OPEN for SHUUD maintenance and its own CI/release decision. No test has been weakened or waived here.

| # | Test | Observed failure / reason | Requirement or boundary | Disposition / evidence required |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Assertion expects `paths:`, `shuud/**`, and `sandbox/**`; observed workflow uses `workflow_dispatch` and has disabled `sandbox-smoke`. | Workflow isolation contract; SHUUD is separate from EAI. | OPEN. Decide whether workflow contract or workflow implementation is canonical; align and rerun the test without weakening the isolation requirement. |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time`. | SHUUD lifecycle timestamp ordering. | OPEN. Trace fixture/event timestamps and lifecycle transitions; prove monotonic ordering with a passing regression test. |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error. | SHUUD incident-to-release lifecycle. | OPEN. Trace request/event timestamps and fix ordering or incorrect fixture; rerun end-to-end test. |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'`. | SHUUD persistence/recovery API response contract. | OPEN. Establish canonical response schema and recovery identifier; test persistence/restart path. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | `AttributeError: '_IncludedRouter' object has no attribute 'path'`. | SHUUD FastAPI route registration inspection. | OPEN. Update route inspection for the supported FastAPI/router API or adjust app composition; verify route table via supported interface. |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` attribute error. | SHUUD route ordering/static mount. | OPEN. Same root cause as #5; prove static mount ordering with a compatible route inspection test. |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path`. | SHUUD DEE release path protection. | OPEN, security-relevant. Identify the unprotected path and add/verify protection; no waiver without a security review and negative test. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt`. | SHUUD economic-impact input validation. | OPEN. Align test cases and public function contract; verify invalid inputs produce the intended validation error. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same two required arguments missing. | Same as #8. | OPEN. Resolve with #8 and retain a separate case assertion. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same two required arguments missing. | Same as #8. | OPEN. Resolve with #8 and retain a separate case assertion. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt`. | Same as #8. | OPEN. Align validation contract and parameterized case. |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles`. | Same as #8. | OPEN. Align validation contract and parameterized case. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected count 1; observed 0. | SHUUD persisted KPI snapshot aggregation. | OPEN. Trace persistence/query filters and prove exactly-once aggregation with fixture-backed evidence. |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected count 1; observed 0. | SHUUD measurement replacement and no-double-count rule. | OPEN. Trace canonical snapshot identity/update semantics and rerun. |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error. | SHUUD measurement summary API. | OPEN. Resolve timestamp ordering and verify API summary. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error. | SHUUD measurement summary aggregation. | OPEN. Resolve timestamp ordering and verify combined summary. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error. | SHUUD timing-only measurement contract. | OPEN. Separate timing validity from optional monetary assumptions; verify timing-only path. |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected validation message regex did not match. | SHUUD economic-input validation contract. | OPEN. Define stable validation error/message and assert the intended behavior. |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error. | SHUUD lifecycle duration and monotonic timestamps. | OPEN. Correct event ordering/fixtures and verify computed durations. |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 `Not Found`. | SHUUD real-process restart route/endpoint. | OPEN. Verify endpoint path and server startup configuration; prove recovery after process restart. |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required argument `status`. | SHUUD sandbox configuration validation. | OPEN. Align constructor/test fixture contract and verify invalid window/threshold rejection. |

## Exact-SHA evidence correction

The PostgreSQL Production Re-performance run `39849400050` is marked successful by the Actions API and its newest artifact is ID `12585247761`; however, the downloaded artifact reports `run_attempt=2`, `github_sha=e872ba14c40be0904260308e626aaab8d0a4c6f7`, and `checked_out_sha=e872ba14c40be0904260308e626aaab8d0a4c6f7`, while the Actions run API reports head SHA `d9c8af8d7b9498ff6c814543112a06d11f73602b`. The artifact's PostgreSQL test log shows 25 tests passed, but this is **not** exact-SHA evidence for d9c8af8. Re-run on a fresh event at the intended SHA and require the artifact manifest SHA to equal both the run head SHA and checked-out `git rev-parse HEAD`.

## Additional diagnostic segments

The same diagnostic bundle shows environment-unconfigured failures in persistence (6), postgres-migration-tests (5 plus 4 errors), postgres-tests (5), production-tests (10), and services (6). The workflow intentionally unsets all `GERCHAIN_*DATABASE*` variables before running those broad diagnostic segments, so database-required tests in those segments are not valid evidence of application pass/fail under a configured PostgreSQL environment. They must be rerun in a correctly configured gate; the observed password-authentication failure and SQLite/PostgreSQL dialect mismatch remain specific items to investigate. The diagnostic job is not a substitute for the dedicated PostgreSQL gates.

## Current decision

- `FINAL LOCK = OPEN`
- `PRODUCTION READY = NOT VERIFIED`
- The 21 tests above remain individually **OPEN**, not waived or fixed.
- No exact-SHA claim is made from an artifact whose tested commit differs from the intended run head.
- Independent re-performance and MG-07 through MG-14 evidence remain required as documented in `docs/MASTER_GATE_PRODUCTION_FINAL_LOCK.md`.
