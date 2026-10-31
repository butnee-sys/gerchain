# Legacy 21-Test Failure Disposition Register

**Status: OPEN — NOT DISPOSITIONED / NOT A FINAL-LOCK EVIDENCE RECORD**

## Purpose and evidence boundary

This register records the 21 failures from the full-repository diagnostic run at commit `0b097bc92746392131cbd412b4aea92638798503` (2026-10-22). The captured diagnostic result was **21 failed, 899 passed, 50 skipped**. These failures must not be represented as fixed merely because later, narrower workflows passed.

The current branch head observed on 2026-10-29 was `27ec09ccd75ad330d4067b452cde72d648502eb8`. That SHA has a passing 56-test core-gates evidence artifact and a passing dedicated SHUUD/SANDBOX product-MVP workflow, but the full root-suite result for that SHA is not yet established here. The core-gates workflow was cancelled; the two broad production/core runs against the older `d9c8af8d7b9498ff6c814543112a06d11f73602b` are not evidence for the current branch head.

**Disposition rule:** every row remains OPEN until a same-SHA test run or a reviewed, explicit scope decision supplies the missing evidence. “Out of core acceptance scope” does not mean “product defect resolved.”

## Same-SHA scope separation and product re-test — 2026-10-30

Candidate SHA: `ec53e8d7abca12377a45a3b2fc8010838036aed6`.

The former failures #2–#21 are SHUUD/SANDBOX product tests, not EAI acceptance criteria. They were rerun in the dedicated [SHUUD and SANDBOX Product MVP Tests workflow](https://github.com/butnee-sys/gerchain/actions/runs/40881444525) at this exact SHA. Retained artifact: `shuud-sandbox-product-evidence-ec53e8d7abca12377a45a3b2fc8010838036aed6` (artifact ID `12915255352`), `junit.xml`.

Verified JUnit result: **108 tests, 0 failures, 0 errors, 1 skipped**. Each of the 20 historical tests listed in rows #2–#21 is present in that JUnit and individually passed. The one skipped test is `test_shuud_survives_postgres_process_restart`, which is not one of the 21 historical failures. This is a successful product-MVP regression result, not a claim that SHUUD/SANDBOX are EAI components or that every product deployment control is closed.

EAI scope is tested separately: the core-gates and production-gate workflows exclude `test_shuud_*.py` and `test_sandbox_*.py` files and retain an explicit exclusion inventory. The remaining item #1, `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated`, is a CI/release-governance contract and remains an **EAI-scope OPEN item** until the same-SHA EAI gate completes with a passing result and retained JUnit/log.

Disposition update:
- #2–#21: **PRODUCT TESTS RE-PASSED; OUT OF EAI ACCEPTANCE SCOPE** — run `40881444525`, artifact `12915255352`, exact SHA above.
- #1: **OPEN — EAI CI/RELEASE GOVERNANCE RETEST PENDING**.
- The original 21 failures remain preserved as historical diagnostics; this section records their current re-test evidence without misclassifying product tests as EAI acceptance failures.

## Individual failures

| # | Exact failing test | Observed failure | Relevant requirement / contract | Current disposition and evidence required |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Expected `paths:` in workflow; workflow used `workflow_dispatch` and had a disabled sandbox-smoke job. | CI/release governance; explicit product/core workflow scope and path-isolation contract. | **OPEN — retest required.** Commit `27ec09c` changes the core scope contract to reflect product exclusions, but the current-SHA core-gates run was cancelled. Capture a passing JUnit result at the selected final SHA and confirm the workflow trigger contract. |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time`. | SHUUD lifecycle chronology and payment-release acceptance. | **OPEN — likely timestamp fixture/order or lifecycle defect; not adjudicated.** Reproduce with exact timestamps, then fix the lifecycle/fixture or document a justified test-contract change and rerun. |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backwards-time `ValueError`. | SHUUD incident-to-escrow end-to-end chronology. | **OPEN.** Need timestamp trace, root cause, code/test change, and same-SHA rerun. |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'`. | API response schema and persistence/recovery contract. | **OPEN.** Establish whether the endpoint response contract or test assumption is wrong; preserve the expected response schema and prove restart recovery. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | `AttributeError: '_IncludedRouter' object has no attribute 'path'`. | Route registration/introspection and FastAPI compatibility. | **OPEN.** Correct route inspection or application route construction; rerun against the pinned dependency set. |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` error. | Route ordering/static mount registration contract. | **OPEN.** Same root-cause investigation as #5, but retain this assertion as an independent regression test. |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path`. | DEE release allowlist, path protection, fail-closed security boundary. | **OPEN — security-relevant.** Do not weaken the guard to make the test pass. Reconcile the release manifest/allowed paths and prove tampered or unprotected paths are denied. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt`. | Economic impact input validation/API signature. | **OPEN.** Determine intended required/optional input contract; test invalid inputs through the public API and rerun. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing required arguments. | Same input-validation contract. | **OPEN.** Must be covered by the same fix as #8 but independently pass. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing required arguments. | Same input-validation contract. | **OPEN.** Must be covered by the same fix as #8 but independently pass. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt`. | Partial economic-input validation. | **OPEN.** Verify the intended paired-input validation is reached rather than Python signature failure. |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles`. | Partial economic-input validation. | **OPEN.** Verify the intended paired-input validation is reached rather than Python signature failure. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one snapshot; observed zero. | KPI snapshot identity, persistence, and economic aggregation. | **OPEN.** Trace snapshot write/read path and prove exactly-once counting with persisted economics. |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one snapshot; observed zero. | Updated-measurement replacement and no-double-count invariant. | **OPEN.** Prove update semantics and aggregation using persisted records. |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backwards-time `ValueError`. | Measurement API chronology and timing/economics summary. | **OPEN.** Identify timestamp source/order and prove valid chronological lifecycle. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backwards-time `ValueError`. | Summary combines valid timing and economic measures. | **OPEN.** Same chronology investigation; rerun this test independently. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backwards-time `ValueError`. | Timing-only summary must not depend on monetary assumptions. | **OPEN.** Fix/validate chronology and prove timing-only mode. |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected “must be supplied together”; got backwards-time error first. | Paired economic inputs must be validated with a deterministic error contract. | **OPEN.** Ensure chronology fixture is valid so the intended economic validation branch is reached, then verify the exact error contract. |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backwards-time `ValueError`. | Operational milestone ordering and duration calculation. | **OPEN.** Add/repair explicit ordered timestamps; verify durations and rejection of genuinely invalid ordering. |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 after process restart. | Restart recovery and endpoint availability/state durability. | **OPEN.** Confirm expected route and startup configuration, then demonstrate state survives a real process restart. |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status`. | Sandbox configuration construction and invalid-window/threshold validation. | **OPEN.** Supply or default the status according to the intended schema, then prove the invalid-window validation is reached and raises the expected error. |

## Cross-cutting root-cause groups (hypotheses, not accepted resolutions)

1. **Timestamp/lifecycle order:** #2, #3, #15–#19. The repeated error suggests a shared fixture or timestamp source/order issue, but a shared cause is not proven until a trace identifies it.
2. **SHUUD API / framework contracts:** #4–#6 and #20. Response shape, route introspection, or route availability may be involved; each assertion still requires explicit evidence.
3. **Economic input and KPI persistence:** #8–#14 and #18. Signature validation, persistence, and aggregation must be checked at their public boundaries.
4. **DEE security allowlist:** #7 is security-relevant and must remain fail-closed.
5. **Workflow scope contract:** #1. The latest recorded change adjusts the scope assertion, but no completed same-SHA core-gates JUnit has been verified here.

## Required closure evidence

For each row, append the disposition, issue/commit reference, exact test command, same-SHA run ID, JUnit/log reference, and reviewer decision. Allowed dispositions are **FIXED AND RE-PASSED**, **TEST CONTRACT CORRECTED WITH JUSTIFICATION AND RE-PASSED**, or **FORMALLY OUT OF SCOPE WITH APPROVED RATIONALE**. “Skipped”, “not run”, a narrower green workflow, or an artifact from a different SHA is not closure evidence.

## Final-lock impact

This register is diagnostic evidence only. It does not prove production readiness, IAM/MFA controls, backup/restore/DR, performance/concurrency limits, restart/recovery operations, legacy authority-store write freeze, or an authorized final-lock decision.

- `FINAL LOCK = OPEN`
- `PRODUCTION READY = NOT VERIFIED`
