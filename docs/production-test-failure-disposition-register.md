# Production test-failure disposition register

**Status:** OPEN — NOT A FINAL-LOCK APPROVAL  
**Observed candidate commit:** `d9c8af8d7b9498ff6c814543112a06d11f73602b`  
**Diagnostic run:** [Production PostgreSQL Gate #39849400091](https://github.com/butnee-sys/gerchain/actions/runs/39849400091)  
**Retained artifact:** `production-postgres-evidence-e872ba14c40be0904260308e626aaab8d0a4c6f7`, artifact ID `12456921635`  
**Evidence report:** `evidence_status=PASS_CANDIDATE`; `commit_sha=checked_out_head_sha=d9c8af8d7b9498ff6c814543112a06d11f73602b`; 13/13 listed source files hashed; migrations 001–017 match; lifecycle JUnit 6 tests, 0 failures/errors/skips. This scoped report does **not** clear the repository regression suite.

## Decision rules

- A failure is not “resolved” merely because another workflow passed or because the test is outside the canonical EAI/CORE release scope.
- SHUUD is a separate application and is excluded from the canonical EAI/CORE release gate by architecture, but its observed failures remain recorded as unresolved SHUUD quality issues unless a documented scope owner approves a disposition.
- No test is deleted, weakened, skipped, or reclassified as passed by this register.
- The earlier segmented diagnostic intentionally unset PostgreSQL environment variables for several database-backed segments. Those missing-environment failures are diagnostic-environment failures and are not included in the 21 root-test failures below. The separate PostgreSQL lifecycle gate has its own DB-backed result.
- Status for all 21 items below is **OPEN — observed failure; no fix or approved waiver evidenced yet**. Owner, corrective commit, rerun result, and approval must be added before closure.

## Per-failure register

| # | Exact test | Observed cause / evidence | Requirement or scope | Disposition / closure evidence |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Assertion expected `paths:`; workflow uses `workflow_dispatch` and has disabled sandbox-smoke job. | Workflow isolation contract; SHUUD workflow scope. | OPEN. Decide intended trigger/isolation contract; update workflow or contract only with reviewed rationale and passing test. |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time`. | SHUUD lifecycle timing invariants. | OPEN. Trace fixture/event timestamps; fix chronology or correct invalid fixture with explicit invariant test; rerun. |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-milestone validation error. | SHUUD HTTP-to-escrow lifecycle. | OPEN. Trace timestamp mapping across API lifecycle; rerun end-to-end. |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'`. | SHUUD persistence/recovery API contract. | OPEN. Define response contract and persistence recovery path; assert incident identity survives restart. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | FastAPI `_IncludedRouter` has no `.path` attribute. | SHUUD route registration/introspection. | OPEN. Adapt route audit to supported FastAPI router representation; retain route-presence assertions. |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same unsupported `.path` access on `_IncludedRouter`. | SHUUD route ordering/static mount. | OPEN. Use supported route flattening/introspection; prove static mount ordering. |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | Security error: release contains an unprotected DEE path. | DEE path protection/security contract. | OPEN. Identify uncovered path; add required protection and positive/negative security tests. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt`. | Economic-impact input validation contract. | OPEN. Align invalid-input test case with API signature or intentionally supported defaults; test validation error. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing required keyword-only arguments. | Economic-impact input validation contract. | OPEN. Same family as #8; preserve distinct case and expected error assertion. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing required keyword-only arguments. | Economic-impact input validation contract. | OPEN. Same family as #8; preserve distinct case and expected error assertion. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing required `vehicle_value_per_minute_mnt`. | Economic-impact input validation contract. | OPEN. Supply/validate intended field and assert correct validation path. |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing required `affected_vehicles`. | Economic-impact input validation contract. | OPEN. Supply/validate intended field and assert correct validation path. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected snapshot count 1, got 0. | SHUUD KPI canonical snapshot and persisted economics. | OPEN. Trace snapshot persistence/aggregation; prove one snapshot is counted once. |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected aggregate count 1, got 0. | SHUUD KPI update/replacement and no-double-count invariant. | OPEN. Fix persistence/aggregation path; test replacement and no double counting. |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-milestone timestamp validation error. | Measurement API timing/economics summary. | OPEN. Trace timestamp conversion and event order; rerun API test. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-milestone timestamp validation error. | Combined timing/economic summary. | OPEN. Correct source timestamps or fixture; preserve chronological invariant. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-milestone timestamp validation error. | Timing-only measurement must not require monetary assumptions. | OPEN. Separate timestamp validity from optional economic assumptions; rerun. |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected validation message not reached because timestamp-order validation fires first. | Validation precedence for incomplete economic inputs. | OPEN. Use chronological fixture and assert missing-economic-input validation explicitly. |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-milestone timestamp validation error. | Operational lifecycle timing/duration invariant. | OPEN. Verify timezone normalization and milestone ordering; rerun duration assertions. |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 Not Found. | SHUUD process-restart route and persisted-state recovery. | OPEN. Identify route/config mismatch; prove persisted state is recovered after real process restart. |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status`. | Sandbox configuration validation/API contract. | OPEN. Align construction contract and invalid-window/threshold test; retain validation coverage. |

## Artifact provenance and SHA notes

1. The lifecycle report from artifact `12456921635` reports candidate `d9c8af8d7b9498ff6c814543112a06d11f73602b` for both `commit_sha` and `checked_out_head_sha`, and `source_hashes_complete=true` with 13 source files and no missing paths.
2. The artifact's displayed name contains `e872ba14c40be0904260308e626aaab8d0a4c6f7`, the synthetic pull-request merge/test tree SHA, not the candidate head SHA. Preserve both identities explicitly: candidate head SHA and tested merge SHA. Do not treat the artifact name as the candidate SHA.
3. The earlier Production Gate attempt reported a stale embedded manifest SHA `5e5193511b47f0815f28a2c6c76fb9f60634b695` and missing evidence files. That artifact is blocked and must not be reused as current-candidate proof. The tracked `docs/production-master-gate-manifest.json` is a source template and must remain SHA-neutral; run-specific manifests must be generated from checked-out HEAD and validated in the retained artifact.
4. PostgreSQL lifecycle JUnit is a narrow 6-test result, not a full-suite JUnit. The root diagnostic remains 21 failed, 899 passed, 50 skipped in the observed run. Terminal Production Gate and core-gates logs/JUnit must be retained and reviewed separately.

## Current gate decision

- **FINAL LOCK = OPEN**
- **PRODUCTION READY = NOT VERIFIED**
- **21 failures = individually recorded; all remain OPEN**
- No final approval is implied by this register.
