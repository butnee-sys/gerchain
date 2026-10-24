# Production Gate Failure Disposition Register

**Status: OPEN — NOT A PRODUCTION-READINESS CERTIFICATE**

- Candidate commit inspected: `d9c8af8d7b9498ff6c814543112a06d11f73602b`
- Final Lock: `OPEN`
- Production Ready: `NOT VERIFIED`
- No failed test is waived by this register. Each entry remains OPEN until a fix or a documented, independently reviewed scope decision is attached to evidence from one immutable candidate SHA.

## Run outcomes and evidence

- Production Gate run: https://github.com/butnee-sys/gerchain/actions/runs/39849399966 — **cancelled**. The full-suite step was cancelled; PostgreSQL evidence capture was skipped; master-gate manifest validation failed.
- core-gates run: https://github.com/butnee-sys/gerchain/actions/runs/39849400130 — **cancelled**. Full repository test suite was cancelled; migration inventory audit was skipped.
- Production Gate artifact ID `12538975777`, attempt 4, contains `production-gate-report.json` with `evidence_status=BLOCKED`, `job_status=cancelled`, missing `migration-history.json` and `postgres-constraints.json`.
- That same artifact's `docs/production-master-gate-manifest.json` reports `checked_out_head_sha=5e5193511b47f0815f28a2c6c76fb9f60634b695`, while the report commit is `d9c8af8d7b9498ff6c814543112a06d11f73602b`. This is a **SHA mismatch**; the embedded manifest is stale and must be regenerated/bound to the exact candidate SHA before it can be accepted.
- Segmented diagnostics artifact ID `12456362962`, from Production PostgreSQL Gate run https://github.com/butnee-sys/gerchain/actions/runs/39849400091, records the root suite as **21 failed, 899 passed, 50 skipped**. These failures remain unresolved in this register. The segmented PostgreSQL test batches also show failures caused by deliberately unset database environment variables; those are not evidence of passing PostgreSQL tests.

## Root-suite failures — individual disposition

All entries below are **OPEN**. “Required proof” means the fix must be tested on the exact candidate SHA; if a test is intentionally out of scope, a reviewer-approved rationale and a corrected test boundary must be documented. No such proof was present in the inspected artifacts.

| # | Test | Observed failure | Requirement area | Required resolution / proof |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Expected workflow `paths:`; current workflow is `workflow_dispatch` and includes a disabled sandbox-smoke job | CI/release governance; SHUUD workflow isolation | Align the contract test with the approved trigger/isolation policy, or restore the required path isolation; rerun test and review workflow diff |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time` | SHUUD lifecycle correctness | Fix timestamp ordering/test fixture; demonstrate monotonic lifecycle and passing test |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error | SHUUD lifecycle / escrow integration | Same as #2, with end-to-end evidence |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: 'incident_id'` | Persistence/restart recovery | Correct API response/state contract or test fixture; prove restart recovery |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | `AttributeError: '_IncludedRouter' object has no attribute 'path'` | API route registration | Update route introspection for the installed FastAPI API or correct route registration; verify exposed routes |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` attribute error | API route ordering | Same as #5; prove static mount order |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path` | DEE security boundary | Protect the required path or correct an invalid release fixture; preserve fail-closed behavior and rerun security proof |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required keyword-only arguments `affected_vehicles` and `vehicle_value_per_minute_mnt` | Economic impact input validation | Reconcile function contract and parameterized test inputs; prove validation behavior |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing required keyword-only arguments | Economic impact input validation | Same as #8 |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing required keyword-only arguments | Economic impact input validation | Same as #8 |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt` | Economic impact input validation | Same as #8 |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles` | Economic impact input validation | Same as #8 |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one canonical snapshot, got zero | KPI integrity / persistence | Fix snapshot persistence/selection or fixture; prove exactly-once aggregation |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one result, got zero | KPI integrity / no double counting | Fix update/aggregation path; prove replacement without duplicate count |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error | Measurement API / lifecycle timing | Correct ordering or fixture; rerun API test |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error | Measurement summary | Same as #15 |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error | Measurement summary / separation of timing and economic assumptions | Same as #15 and prove timing-only mode |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected error-message regex did not match | Economic input validation | Align stable error contract and test; prove incomplete inputs fail closed |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error | Operational timing | Correct chronology/fixture and verify computed durations |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 after process restart | Restart recovery / route or state restoration | Identify missing endpoint/state restoration and demonstrate successful real-process restart |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status` | Sandbox configuration validation | Align constructor/schema and test fixture; prove invalid windows/thresholds are rejected |

## Other blocking evidence gaps

These are additional blockers, not counted among the 21 root-suite failures:

1. **Database test environment and connectivity:** segmented persistence, postgres, migration and production batches show failures from missing `GERCHAIN_DATABASE_URL`, `GERCHAIN_POSTGRES_DSN`, `GERCHAIN_TEST_DATABASE_URL`, or `GERCHAIN_MIGRATION_TEST_DATABASE_URL`; one connection attempt reports PostgreSQL password authentication failure for user `gerchain`. Provide a properly configured isolated PostgreSQL environment and rerun the applicable suites; do not treat env-missing failures as passes.
2. **Service/schema test failures:** six service tests failed in the same diagnostics: SQLite cannot parse PostgreSQL-specific `schema[0]` SQL; a missing-columns assertion has a regex mismatch; a constraint test expects `>=0` but sees `>=`; and the self-repair test's source did not match the approved repair template. These need individual fixes/dispositions and proof.
3. **Manifest binding:** regenerate the production master-gate manifest from the exact checkout; verify `commit_sha`, `checked_out_head_sha`, expected SHA and all evidence hashes are identical and validated.
4. **PostgreSQL evidence:** the latest inspected Production Gate artifact is blocked and lacks migration history and constraint evidence because the gate was cancelled/skipped. Capture and retain those files from a completed successful run.
5. **IAM/MFA, privileged access, authority-store freeze, observability, recovery/restart/no-duplicate movement, production-like performance/concurrency, backup/restore/DR, release governance, independent re-performance, complete evidence index and authorized final decision:** no sufficient retained evidence for all these requirements was established by the inspected artifacts. Each requires owner, evidence URI/hash, candidate SHA, reviewer and pass/fail decision.

## Acceptance rule

Do not set `PASS_CANDIDATE`, `PRODUCTION READY`, or `FINAL LOCK` based on these runs. First fix or formally disposition every failure; rerun full and database-backed suites on one immutable candidate SHA; generate a fresh artifact whose report, source hashes, migration checksums, checked-out SHA and master-gate manifest agree; complete independent re-performance and all operational/security evidence; then record an explicit authorized final decision.
