# Production Final-Lock Audit Register — 21 Root-Suite Failures

Status: **OPEN — FINAL LOCK NOT GRANTED**
Candidate under audit when these failures were captured: `d9c8af8d7b9498ff6c814543112a06d11f73602b`.
Evidence source: Production PostgreSQL Gate run [39849400091](https://github.com/butnee-sys/gerchain/actions/runs/39849400091), artifact `production-postgres-evidence-e872ba14c40be0904260308e626aaab8d0a4c6f7`, file `segmented-tests/root-tests.log`.
Observed result: **21 failed, 899 passed, 50 skipped**. These failures have not been demonstrated as resolved. Suspected requirements below are triage classifications based on test names and exception output; they are not a substitute for an approved requirement-to-test trace.

## Failure-by-failure register

| # | Failed test | Observed failure / likely cause | Requirement area to verify | Disposition / evidence |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Contract test expects `paths:`; workflow currently uses `workflow_dispatch` and includes a disabled sandbox-smoke job. | CI workflow isolation and intended SHUUD trigger contract. | OPEN — decide and document intended workflow contract; update workflow or test only after review; rerun test. |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time`. | SHUUD lifecycle timestamps and valid test fixture ordering. | OPEN — inspect milestone payload/order; fix implementation or fixture against the intended invariant; rerun. |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error. | End-to-end incident-to-escrow lifecycle timing. | OPEN — trace generated timestamps through API path; rerun. |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'`. | API response contract and persistence/recovery identifiers. | OPEN — capture actual response schema and correct producer/consumer contract; rerun. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | `AttributeError: '_IncludedRouter' object has no attribute 'path'`. | FastAPI router registration/introspection compatibility. | OPEN — validate route registration using supported FastAPI API; rerun. |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` error. | Route ordering and static mount placement. | OPEN — inspect route ordering using supported router structures; rerun. |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path`. | DEE release path protection / root-of-trust policy. | OPEN — identify missing protected path and verify policy coverage; no security bypass permitted; rerun. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt`; TypeError occurs before expected validation. | Economic impact input validation API. | OPEN — align test cases and function validation contract; preserve explicit validation errors; rerun. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing-argument TypeError. | Economic impact input validation API. | OPEN — same triage as #8; demonstrate expected error type/message. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing-argument TypeError. | Economic impact input validation API. | OPEN — same triage as #8; demonstrate expected error type/message. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt`. | Economic impact input validation API. | OPEN — same triage as #8; demonstrate expected error type/message. |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles`. | Economic impact input validation API. | OPEN — same triage as #8; demonstrate expected error type/message. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Assertion `0 == 1`. | KPI snapshot persistence, uniqueness and aggregation. | OPEN — trace snapshot writes/reads and aggregation query; rerun. |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Assertion `0 == 1`. | KPI update semantics and duplicate-count prevention. | OPEN — verify replacement/upsert and aggregation behavior; rerun. |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error. | Measurement summary API timing/economic composition. | OPEN — trace fixture timestamps and combined summary behavior; rerun. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error. | Measurement summary invariants. | OPEN — verify milestone chronology and calculation path; rerun. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error. | Timing-only measurement must not require monetary assumptions. | OPEN — correct chronology issue and revalidate timing-only mode. |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected “must be supplied together” message did not match; timestamp validation fired first. | Economic input completeness validation and validation ordering. | OPEN — isolate validation stages and verify deterministic error contract. |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error. | Operational milestone order and duration calculation. | OPEN — correct timestamp fixture or logic based on intended chronology; rerun. |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 `{"detail":"Not Found"}`. | Restart recovery endpoint and persisted state visibility. | OPEN — identify requested route and startup/recovery state; rerun with evidence. |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status`. | Sandbox configuration validation and constructor contract. | OPEN — reconcile test construction with public config API; retain intended invalid-window validation; rerun. |

## SHA and artifact integrity

- The migration lifecycle report in artifact `12456921635` reports `source_hashes_complete: true` and `source_missing: []`, and its checked-out SHA was recorded as `d9c8af8d7b9498ff6c814543112a06d11f73602b`. However, the JSON file contains trailing extra data and is not valid single-document JSON; retain and fix the artifact/report format before treating it as a clean machine-verifiable certificate.
- The downloaded `production-gate-evidence` artifact `12457545216` for run `39849400050` records `github_sha` and `checked_out_sha` as `e872ba14c40be0904260308e626aaab8d0a4c6f7`, whereas the currently inspected run metadata for that run identifies head SHA `d9c8af8d7b9498ff6c814543112a06d11f73602b` and run attempt 2. Treat the downloaded artifact as stale/attempt-mismatched until the exact attempt's artifact and logs are verified. Do not combine it with d9c8af8 evidence.
- The Exact-SHA manifest artifact `12456762135` records `d9c8af8d7b9498ff6c814543112a06d11f73602b` and migration hashes for versions 001–017, but lists generated `__pycache__` files as modified in `git_status_porcelain`. This needs a documented clean-worktree policy or an improved artifact step before final certification.

## Cancelled runs

- [Production Gate run 39849399966](https://github.com/butnee-sys/gerchain/actions/runs/39849399966), latest observed attempt 9: conclusion `cancelled`.
- [core-gates run 39849400130](https://github.com/butnee-sys/gerchain/actions/runs/39849400130), latest observed attempt 12: conclusion `cancelled`.
- Their downloaded job logs end with `##[error]The operation was canceled.` and process cleanup. The available log does not identify the actor or authoritative cancellation reason; do not infer one. Both logs show the test process was still active when cancellation occurred, so neither is a completed final result.

## Required closure evidence

1. For every row above, attach a passing rerun or an approved, requirement-linked disposition with reviewer and rationale; do not suppress tests to manufacture a green result.
2. Regenerate reports as valid JSON, with `run_id`, `run_attempt`, `github_sha`, `checked_out_sha`, source file list and hashes, migration inventory/history, and a SHA-256 of the report itself.
3. Re-run all required gates on one frozen candidate commit and verify every artifact belongs to that exact SHA and attempt.
4. Produce explicit evidence for IAM/MFA, privileged access review, restart/recovery/no-duplicate value movement, performance/concurrency, backup/restore and disaster recovery.
5. Obtain independent re-performance and authorized release approval.
6. Until all above are verified: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.
