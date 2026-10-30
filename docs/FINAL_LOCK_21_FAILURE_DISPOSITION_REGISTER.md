# 21 Failure Disposition Register — EAI/CORE candidate

**Register status:** OPEN — no failure is represented as resolved.  
**Observed candidate SHA:** `d9c8af8d7b9498ff6c814543112a06d11f73602b`  
**Diagnostic source:** Production PostgreSQL Gate run `39849400091`, artifact `12456921635`, `segmented-tests/root-tests.log`.  
**Observed diagnostic result:** 21 failed, 899 passed, 50 skipped.  
**Scope note:** These failures are in SHUUD/SANDBOX and adjacent tests, which the independent EAI audit explicitly excludes from EAI scope. That exclusion is not a resolution of the failures and must not be used to certify SHUUD.

## Individual disposition

All rows remain **OPEN / NOT RESOLVED** until a subsequent run on the same candidate SHA contains a passing test or an approved, documented scope decision with an accountable approver.

| # | Test | Observed failure | Requirement / impact area | Required disposition and evidence | Status |
|---:|---|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Contract expects `paths:`; workflow uses `workflow_dispatch` and disabled sandbox-smoke job | Workflow isolation / CI governance | Decide intended trigger contract; align workflow or contract test without weakening isolation; rerun contract test | OPEN |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time` | SHUUD lifecycle chronology | Trace fixture/event timestamps and validation; prove valid lifecycle reaches release | OPEN |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error | SHUUD incident-to-escrow lifecycle | Fix chronology source/order; rerun end-to-end with persisted timestamps | OPEN |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'` | API response contract / recovery | Correct response schema or consumer expectation; prove recovery after process state loss | OPEN |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | FastAPI `_IncludedRouter` has no `.path` attribute | Route registration / framework compatibility | Inspect route enumeration against installed FastAPI version; assert routes via supported API | OPEN |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` assumption | Route ordering / static mount safety | Replace unsupported introspection and verify static mount remains last | OPEN |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path` | DEE release-path protection | Identify uncovered path and add required protection; rerun trust/transparency proof | OPEN |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | Economic impact input validation | Align test vectors/API signature; preserve required-input validation and prove expected error | OPEN |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing two keyword-only inputs | Economic impact input validation | Same as #8; separate parameter case must pass | OPEN |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing two keyword-only inputs | Economic impact input validation | Same as #8; separate parameter case must pass | OPEN |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt` | Economic impact input validation | Align this parameter case with function contract and assert validation outcome | OPEN |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles` | Economic impact input validation | Align this parameter case with function contract and assert validation outcome | OPEN |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one canonical snapshot; observed zero | KPI persistence / canonical snapshot accounting | Trace snapshot persistence and aggregation; prove exactly-once count | OPEN |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one snapshot; observed zero | KPI update / duplicate prevention | Prove update replaces prior value and avoids double count | OPEN |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error | Measurement API chronology | Fix fixture/event time sequence; prove timing and economics response | OPEN |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error | Measurement summary chronology | Correct timestamp ordering and rerun combined summary | OPEN |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error | Timing-only measurement | Ensure timing-only path does not require economic assumptions; prove valid chronology | OPEN |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected paired-input validation message; chronology error occurred first | Economic input validation / validation ordering | Ensure input validation is deterministic and occurs before unrelated chronology failure; rerun | OPEN |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error | Operational milestone chronology | Fix lifecycle timestamps and prove nonnegative durations | OPEN |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 Not Found | Process restart / route persistence | Identify missing route or restart wiring; prove endpoint works after real process restart | OPEN |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status` | Sandbox configuration contract | Update fixture/callers or documented default; preserve invalid-window/threshold validation | OPEN |

## Artifact integrity and run disposition

- Artifact `12456921635` from run `39849400091` binds `commit_sha` and `checked_out_head_sha` to `d9c8af8d7b9498ff6c814543112a06d11f73602b`; reports `evidence_status=PASS_CANDIDATE`, 17/17 migration files, matching file/database checksums, `source_hashes_complete=true`, 13 source files, no missing source files, and lifecycle JUnit 6 tests / 0 failures / 0 errors / 0 skipped. This is a migration-lifecycle candidate report only; it does not erase the 21 failures above.
- Artifact `12456762135` from Exact-SHA run `39849400071` declares the same `d9c8af8...` commit and lists all 17 migration hashes. Its `git_status_porcelain` records modified tracked `__pycache__` files; this is an artifact cleanliness warning that requires explanation/remediation.
- Artifact `12456442917` from EAI PostgreSQL re-performance run `39849399950` records `d9c8af8...`, migration history 1–17, PostgreSQL 16.15, runtime boot and reconciliation artifacts. The run conclusion was success.
- Artifact `12457545216` (run `39849400050`) is **INVALID FOR THE d9c8af8 CANDIDATE**: its embedded `github_sha`, `checked_out_sha`, `tested_commit`, and `tested-commit.txt` state `e872ba14c40be0904260308e626aaab8d0a4c6f7`, not the run's expected candidate SHA. Do not use it as d9c8af8 evidence. Retain it as quarantined historical evidence; obtain a fresh run and artifact with every embedded SHA equal to the selected candidate.
- The two mandatory broad runs `39849399966` (Production Gate) and `39849400130` (core-gates) ended **cancelled** on `d9c8af8...`; they are not passing evidence and must be rerun on a new, single candidate commit.

## Required closure criteria

1. Resolve or formally disposition all 21 rows, with test-level evidence and accountable approval where scope exclusion is claimed.
2. Quarantine mismatched artifact `12457545216`; regenerate all evidence with embedded SHA equal to the selected candidate SHA.
3. Remove or explain generated tracked `__pycache__` modifications in the Exact-SHA artifact; require clean checkout evidence.
4. Run Production Gate, core-gates, independent audit, PostgreSQL re-performance and exact-SHA checks on one immutable commit; archive final logs, JUnit, reports and checksums.
5. Complete remaining IAM/MFA, legacy-authority write-freeze, observability/recovery, performance/concurrency, backup/restore/DR, release governance and independent re-performance evidence.
6. Keep `FINAL LOCK = OPEN` and `PRODUCTION READY = NOT VERIFIED` until all gates and authorized sign-off are evidenced.

**No production-ready certification or final lock is granted by this register.**
