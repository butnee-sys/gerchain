# Regression disposition register — 2026-10-31

## Decision state

- `FINAL LOCK = OPEN`
- `PRODUCTION READY = NOT VERIFIED`
- This register is an evidence ledger, not an approval or waiver.
- No failure below is marked fixed, accepted, waived, or out of scope. Each remains **OPEN** until a fix commit and passing same-SHA rerun, or a written disposition by an authorized decision-maker, is attached.
- Canonical EAI architecture separates SHUUD/SHIID from EAI prerequisites. That boundary is relevant to scope review, but does not itself waive a repository-wide regression failure.

## Evidence provenance

- The 21-failure baseline is the root test segment from the Production PostgreSQL Gate diagnostic artifact at commit `0b097bc92746392131cbd412b4aea92638798503`: `root-tests.log`, result `21 failed, 899 passed, 50 skipped`.
- A later full-suite attempt at `d9c8af8d7b9498ff6c814543112a06d11f73602b` did **not** produce a completed JUnit report. Production Gate run [39849399966](https://github.com/butnee-sys/gerchain/actions/runs/39849399966), attempt 17, was cancelled after running from 01:04:59Z to 07:05:23Z on 2026-10-31. Its test step was cancelled; therefore the earlier 21 are not yet confirmed as either still failing or fixed at this SHA.
- [core-gates run 39849400130](https://github.com/butnee-sys/gerchain/actions/runs/39849400130) was also cancelled. The full-repository-suite step was cancelled; earlier migration concurrency and canonical architecture steps succeeded.
- The Production Gate artifact [13034446196](https://github.com/butnee-sys/gerchain/actions/runs/39849399966) reports `evidence_status=BLOCKED`, `job_status=cancelled`, and missing `migration-history.json` and `postgres-constraints.json`. It does not contain JUnit.
- The same artifact bundles `docs/production-master-gate-manifest.json` whose embedded `checked_out_head_sha` / `commit_sha` is `5e5193511b47f0815f28a2c6c76fb9f60634b695`, not the run SHA `d9c8af8...`. Treat this as stale, non-current evidence; do not bind it to the d9c8af8 run.
- Run 39849399966's six-hour elapsed execution and cancellation are consistent with a job timeout, but the available run metadata does not explicitly state the cancellation initiator/reason. Confirm via workflow timeout/runner cancellation metadata before recording a definitive cause.

## 21 baseline failures — individual disposition

All rows have status **OPEN — NO FIX COMMIT / NO AUTHORIZED DISPOSITION**. Requirement mapping below is a provisional classification from the test's name and failure; it is not a formal requirements traceability approval.

| # | Test | Observed failure | Provisional requirement area | Required closure evidence |
|---:|---|---|---|---|
| 1 | `tests/test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` | Assertion expects workflow `paths:`; actual workflow uses `workflow_dispatch` and has disabled sandbox-smoke job | Workflow isolation / scope boundary | Correct contract test or workflow design; approved SHUUD/EAI scope decision; same-SHA pass |
| 2 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | `ValueError: operational milestones cannot move backward in time` | SHUUD lifecycle time ordering | Reproducible lifecycle fix/test fixture; same-SHA pass |
| 3 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backward-time validation error | SHUUD API lifecycle | Fix/test fixture and same-SHA pass |
| 4 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | `KeyError: incident_id` | SHUUD persistence/recovery contract | API response/schema and restart recovery proof; same-SHA pass |
| 5 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | FastAPI `_IncludedRouter` has no `.path` | SHUUD route registration | Version-compatible route introspection or app fix; same-SHA pass |
| 6 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same `_IncludedRouter.path` attribute error | SHUUD route ordering | Route ordering verification with supported API; same-SHA pass |
| 7 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | `SecurityError: release contains an unprotected DEE path` | DEE release-path protection | Protect the path or document and approve a valid exception; security test pass |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Missing required `affected_vehicles` and `vehicle_value_per_minute_mnt` | Economic impact input validation | Align API contract/test input; same-SHA pass |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Missing same two required keyword-only arguments | Economic impact input validation | Align API contract/test input; same-SHA pass |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Missing same two required keyword-only arguments | Economic impact input validation | Align API contract/test input; same-SHA pass |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Missing `vehicle_value_per_minute_mnt` | Economic impact input validation | Align API contract/test input; same-SHA pass |
| 12 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Missing `affected_vehicles` | Economic impact input validation | Align API contract/test input; same-SHA pass |
| 13 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one KPI snapshot; observed zero | KPI snapshot integrity | Correct persistence/aggregation or fixture; same-SHA pass |
| 14 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected one KPI snapshot; observed zero | KPI update/idempotency | Correct snapshot replacement/aggregation; same-SHA pass |
| 15 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backward-time validation error | Measurement API time ordering | Correct timestamp sequencing/validation; same-SHA pass |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backward-time validation error | Measurement summary | Correct timestamp sequencing/fixture; same-SHA pass |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backward-time validation error | Timing-only measurement | Decouple timing-only path from invalid ordering; same-SHA pass |
| 18 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Expected validation regex did not match | Economic input validation | Stable documented validation error and test; same-SHA pass |
| 19 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Backward-time validation error | Operational timing | Correct milestone ordering/time source; same-SHA pass |
| 20 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | HTTP 404 after restart | Process restart/API route recovery | Reproducible process-level recovery proof; same-SHA pass |
| 21 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | `SandboxConfig.__init__()` missing required `status` | Sandbox configuration validation | Correct defaults/schema or test fixture; same-SHA pass |

## Separate diagnostics — not part of the 21 root failures

The segmented diagnostics also reported failures/errors in persistence (6, DB environment variables absent), postgres-migration (5 failures + 4 errors, DB environment variables absent), postgres-tests (5 failures, including absent DB variables and missing inventory report), production tests (10 failures, mainly DB environment/configuration; one password authentication failure), and services (6 failures including SQLite/PostgreSQL syntax mismatch, absent DB variable, and self-repair template mismatch). These are separate groups and must not be silently folded into or counted as the 21 root failures. Re-run each with correctly provisioned isolated databases and retain JUnit/log artifacts.

## Closure protocol

1. Re-run the full test suite and produce JUnit on a single candidate SHA. Do not infer current status from the older 0b097bc baseline.
2. For each of the 21 rows, record one of: (a) fix commit SHA + relevant passing test evidence on the candidate SHA; or (b) authorized written disposition identifying owner, requirement, rationale, residual risk, and approval reference. A scope boundary alone is not an approval.
3. Correct the stale embedded master-gate manifest and regenerate evidence from the checked-out candidate SHA. Bind every report, migration history, constraint inventory, source-file hash, JUnit report, and checksum manifest to that SHA and run attempt.
4. Ensure PostgreSQL tests receive the documented isolated DSNs; do not treat tests skipped or failed because of absent credentials as passed.
5. Complete independent re-performance and the remaining production controls (IAM/MFA, legacy authority write-freeze, observability/recovery, performance/concurrency, backup/restore/DR, release governance, final evidence index and authorized decision).
6. Only then may an authorized decision-maker consider final lock.

**Current decision remains: FINAL LOCK = OPEN; PRODUCTION READY = NOT VERIFIED.**
