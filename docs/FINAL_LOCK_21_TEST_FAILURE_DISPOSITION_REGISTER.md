# Historical 21-Test Failure Disposition Register

**Disposition status: OPEN — none of these 21 failures is recorded as fixed or formally waived.**  
**Source run:** [Production PostgreSQL Gate, run 39849400091](https://github.com/butnee-sys/gerchain/actions/runs/39849400091), diagnostic archive artifact `12456362962`, historical candidate `d9c8af8d7b9498ff6c814543112a06d11f73602b`.  
**Observed suite result:** `21 failed, 899 passed, 50 skipped`.  
**Scope rule:** The Master Gate defines SHUUD as a separate application, outside the EAI production-lock boundary. That scope distinction does not make SHUUD failures “passed”; they remain SHUUD acceptance blockers until repaired or explicitly dispositioned by the responsible owner. The workflow-isolation contract test remains an EAI/CI boundary requirement.

| # | Exact failing test | Observed failure | Requirement / boundary | Current disposition | Closure evidence required |
|---:|---|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Expected `paths:` in SHUUD workflow; actual workflow is `workflow_dispatch` only and sandbox-smoke job is disabled | CI workflow must enforce the approved SHUUD/EAI boundary and intended trigger isolation | **OPEN — in-scope contract mismatch; not waived** | Reconcile test with approved workflow policy; retain a passing contract test proving the chosen trigger/isolation rule |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time` | SHUUD lifecycle timestamps must be monotonic and lifecycle fixture must satisfy the contract | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Correct lifecycle/fixture or implementation; passing targeted test and JUnit |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | `ValueError: operational milestones cannot move backward in time` | Incident-to-release end-to-end lifecycle timing | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Passing end-to-end test with ordered, timezone-aware milestones |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'` | Persistent incident response must preserve the canonical incident identifier | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Fix response/persistence contract; passing restart/state-loss test |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | `AttributeError: '_IncludedRouter' object has no attribute 'path'` | Route registration inspection must match supported FastAPI router behavior | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Inspect routes using supported API; verify lifecycle/sandbox routes via test client |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | `AttributeError: '_IncludedRouter' object has no attribute 'path'` | Static mount ordering must not shadow application routes | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Replace brittle router introspection and prove static mount ordering |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path` | Every required DEE release path must be protected by the root-of-trust policy | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Correct route protection or release policy; passing negative and positive security tests |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt` | Economic impact input validation contract | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Align test/API signature without weakening validation; passing targeted test |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt` | Economic impact input validation contract | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Same validation matrix must pass for this input case |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt` | Economic impact input validation contract | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Same validation matrix must pass for this input case |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing required keyword-only argument `vehicle_value_per_minute_mnt` | Partial economic inputs must be rejected consistently | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Passing targeted test showing expected validation error |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing required keyword-only argument `affected_vehicles` | Partial economic inputs must be rejected consistently | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Passing targeted test showing expected validation error |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one canonical snapshot; observed `0` | KPI aggregation must count a persisted canonical snapshot exactly once | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Fix snapshot query/fixture; prove exact-once aggregation with persisted data |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one updated measurement; observed `0` | Updated economic measurements must replace prior values without double counting | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Passing replacement/idempotency test and aggregation report |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | `ValueError: operational milestones cannot move backward in time` | Measurement API must accept valid chronological lifecycle evidence and reject invalid order | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Fix fixture or implementation; pass chronological and backward-time cases |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | `ValueError: operational milestones cannot move backward in time` | Combined timing/economic summary must process valid milestones | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Passing summary test with ordered milestones |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | `ValueError: operational milestones cannot move backward in time` | Timing-only measurement must not require monetary assumptions and must validate chronology | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Passing timing-only test with valid timestamps |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected “must be supplied together”; chronology error occurred first | Economic-input validation must produce the intended validation result independently of timestamp fixtures | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Fix fixture/order of validation and assert the intended error message |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | `ValueError: operational milestones cannot move backward in time` | Lifecycle duration calculation requires chronological milestones | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Correct timestamp sequence or logic; passing duration and timezone tests |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | `AssertionError: HTTP 404: {"detail":"Not Found"}` | Restarted SHUUD process must expose the expected persisted-resource endpoint | **PASS EVIDENCE ON d371daa; OPEN for current-SHA revalidation** | Correct route/configuration or test contract; passing real-process restart test |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `TypeError: SandboxConfig.__init__() missing 1 required positional argument: 'status'` | Sandbox configuration constructor and invalid-window/threshold validation contract | **OPEN — SHUUD acceptance** | Align fixture/API initialization and prove invalid configuration is rejected as intended |

## Evidence and decision rules

- This is a historical failure register, not a claim that these tests still fail on the current candidate.
- The 20 SHUUD tests (#2–#21) may be excluded from the **EAI-only** lock gate only under the documented application boundary; they remain open for SHUUD release acceptance and are not marked passed.
- Test #1 remains in scope because it validates CI/workflow boundary isolation.
- Close a row only with a linked fix commit and a passing targeted JUnit/log at that commit, or an explicit, reviewable scope decision by the responsible authority. A new SHA requires rerunning the relevant verification.
- No failures are silently suppressed, converted to skips, or counted as successful.


## Follow-up verification on candidate d371daa (2026-10-30)

This section supplements, and does not erase, the historical d9c8af8 failure record.

- Candidate: `d371daa4263be8736e0c2ca782f09cf06f8d02b2`.
- Separate SHUUD/SANDBOX product workflow: [run 40976839068](https://github.com/butnee-sys/gerchain/actions/runs/40976839068), JUnit artifact `12942773525`.
- JUnit result: 108 tests; 107 passed, 0 failed, 0 errors, 1 skipped.
- A test-inventory cross-check recorded in PR #111 comment [6516223987](https://github.com/butnee-sys/gerchain/pull/111#issuecomment-6516223987) matched 20 of the 21 historical failures (#2–#21) to passing tests in that product workflow. Accordingly, those 20 rows have **PASS EVIDENCE ON d371daa**; they are not declared permanently closed because the current branch head is later than d371daa and needs same-SHA rerun.
- Row #1 (`test_shuud_workflows_are_path_isolated`) is not in that product-workflow JUnit. It remains **OPEN** pending an explicit approval of the changed workflow-isolation contract or a corrected contract test and passing run.
- The product workflow had one skipped test, `tests.test_shuud_process_restart_postgres_e2e::test_shuud_survives_postgres_process_restart`. It is a separate outstanding PostgreSQL-enabled SHUUD check; it is not counted as one of the 20 passing historical failures.

### Row-level follow-up disposition

| Historical rows | Candidate d371daa evidence | Current branch disposition |
|---|---|---|
| #2–#21 | Matching SHUUD/SANDBOX tests present and passing in run 40976839068, JUnit artifact 12942773525 | PASS EVIDENCE ON d371daa; **OPEN for revalidation on current frozen SHA** |
| #1 | Not present in product-workflow JUnit; workflow-contract difference remains | **OPEN — explicit policy approval or corrected contract test required** |

No historical failure is silently waived. A later candidate must rerun the relevant tests and attach JUnit/log evidence bound to that exact SHA before these rows can be closed for release.
