# Legacy 21-failure disposition register

**Status:** INITIAL TRIAGE ONLY — no fixes or closures are claimed.
**Origin run:** segmented diagnostic run at commit `0b097bc92746392131cbd412b4aea92638798503`.
**Source:** retained `segmented-test-diagnostics.zip`, specifically `root-tests.log`.
**Observed result:** 21 failed, 899 passed, 50 skipped. This is a historical diagnostic result, not a result for the current PR head.
**EAI scope note:** the failing cases below are SHUUD/product tests plus one workflow-isolation contract test. The later canonical architecture records describe SHUUD as a separate product, outside EAI acceptance. That scope distinction does not make the failed tests pass; they require a separately owned disposition.

| # | Exact failing test | Observed failure | Candidate requirement / owner boundary | Closure evidence required | Status |
|---:|---|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Expected workflow text to contain `paths:`; actual workflow is `workflow_dispatch` and has disabled sandbox-smoke job | Workflow isolation contract; CI governance | Decide intended trigger contract; update workflow or test only with approved rationale; rerun this exact test and capture log | OPEN |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time` | SHUUD lifecycle timestamp ordering | Reproduce with deterministic timestamps; establish valid ordering semantics; pass exact test and lifecycle suite | OPEN |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error | SHUUD HTTP-to-escrow lifecycle | Reproduce request timeline; fix or correct invalid fixture with rationale; pass exact E2E test | OPEN |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: incident_id` | SHUUD persistence/recovery API contract | Identify missing response/persisted field; assert durable incident identity after restart; pass restart E2E test | OPEN |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | FastAPI `_IncludedRouter` has no `.path` attribute | SHUUD route registration / framework compatibility | Inspect supported route introspection API and app route tree; verify expected endpoints over ASGI; pass exact test | OPEN |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` introspection error | SHUUD route ordering | Test actual route order using supported FastAPI representation; pass exact test | OPEN |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path` | SHUUD/DEE release path protection | Enumerate required protected paths; prove each path is protected and unauthorized release fails closed; pass security E2E | OPEN |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | SHUUD economic-impact input contract | Define required/optional inputs; align test call and public signature; verify validation error and valid calculation | OPEN |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same two missing required keyword-only arguments | Same as #8 | Same evidence as #8, with this parameter case explicitly passing | OPEN |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same two missing required keyword-only arguments | Same as #8 | Same evidence as #8, with this parameter case explicitly passing | OPEN |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt` | Same as #8 | Verify this partial-input case is rejected for the intended reason; pass exact case | OPEN |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles` | Same as #8 | Verify this partial-input case is rejected for the intended reason; pass exact case | OPEN |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected 1 snapshot, observed 0 | SHUUD KPI snapshot persistence/aggregation | Trace write/read path and snapshot identity; prove exactly one persisted snapshot is counted once | OPEN |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected 1 snapshot, observed 0 | SHUUD KPI update semantics | Prove replacement semantics and no double counting across persisted update; pass exact test | OPEN |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error | SHUUD measurement API / lifecycle ordering | Deterministic event timeline; verify summary exposes expected timing and economic fields | OPEN |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error | SHUUD measurement summary | Valid ordered event fixture and expected combined summary; pass exact test | OPEN |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error | SHUUD timing-only measurement contract | Prove timing-only path does not require monetary assumptions and uses valid timestamps | OPEN |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected validation message did not match | SHUUD economic input validation | Freeze required-input contract and assert stable, specific error; pass exact test | OPEN |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error | SHUUD operational milestone chronology | Define event ordering and duration rules; test complete lifecycle with deterministic timestamps | OPEN |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 Not Found | SHUUD process restart / route availability | Identify missing route or incorrect URL; prove persisted state and endpoint survive a real process restart | OPEN |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status` | SHUUD sandbox configuration contract | Define whether status is required/defaulted; validate invalid window/threshold ordering with explicit config; pass exact test | OPEN |

## Cross-cutting diagnosis

The log supports these observed clusters, but does not by itself establish the underlying code root cause:

1. **Timestamp ordering:** tests 2, 3, 15, 16, 17, 19.
2. **HTTP/API and persistence contract:** tests 4, 5, 6, 20.
3. **DEE release protection:** test 7.
4. **Economic input contract:** tests 8–12, 18.
5. **KPI persistence/aggregation:** tests 13–14.
6. **Sandbox configuration contract:** test 21.
7. **Workflow trigger/isolation expectation:** test 1.

## Disposition rules

A test may be closed only by one of:
- **FIXED:** code change identified by commit; exact test and relevant regression suite pass on that same commit; retained JUnit/log attached.
- **SCOPE-EXCLUDED:** explicit product/acceptance boundary approved and recorded by the responsible owner; the test remains visible as a product defect or deferred obligation and is not counted as a passing test.
- **TEST-CORRECTED:** evidence proves the assertion/fixture was invalid; rationale and revised test are committed; relevant behavior remains covered.
- **BLOCKED:** dependency, environment, or credentials unavailable; exact missing prerequisite and responsible owner recorded. A blocked test is not a pass.

No row is closed by this initial register. Do not infer that these 21 historical failures are present or absent on a later SHA without rerunning them. Do not combine this older SHA's results with newer commit evidence.

## Required next evidence

1. Recover and retain the complete original JUnit XML if available; the segmented log is currently the direct source for the 21 named failures.
2. For each row, add owner, linked issue/PR, fix commit (if any), rerun run ID, JUnit testcase result, and reviewer disposition.
3. Run the relevant SHUUD/product suite independently from EAI acceptance; keep its result distinct from the EAI exact-SHA gate.
4. Record any scope exclusion explicitly; never convert an exclusion into a green test.
5. Keep production final lock open until all applicable production gates and authorized approval are evidenced on one immutable candidate SHA.

**Current decision:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.
