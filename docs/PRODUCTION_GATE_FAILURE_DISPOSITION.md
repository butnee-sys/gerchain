# Production Gate Failure Disposition Register

**Current status: OPEN — FINAL LOCK NOT GRANTED.**  
**Scope:** evidence triage for the prior segmented diagnostic run and the latest rerun. This register does not claim the listed SHUUD defects are fixed. SHUUD is explicitly a separate application and outside the GerChain EAI production assurance boundary; the failures remain open for the SHUUD workstream unless separately retested and closed.

## Run identity and evidence

- Historical segmented run: [Production PostgreSQL Gate 39848633633](https://github.com/butnee-sys/gerchain/actions/runs/39848633633), commit `0b097bc92746392131cbd412b4aea92638798503`.
- Prior diagnostic count: 21 failed, 899 passed, 50 skipped.
- Latest segmented run: [Production PostgreSQL Gate 40105612612](https://github.com/butnee-sys/gerchain/actions/runs/40105612612), commit `ab9799cd41e32d04836d6d26a5026f9517f60a73`.
- Latest root diagnostic count: 20 failed, 900 passed, 50 skipped.
- Latest PostgreSQL lifecycle evidence: artifact `12564831076`; report records `evidence_status=PASS_CANDIDATE`, `commit_sha=checked_out_head_sha=ab9799cd41e32d04836d6d26a5026f9517f60a73`, 17/17 migration checksums matching, 13/13 source hashes present, JUnit 6 tests / 0 failures / 0 errors / 0 skipped.
- Latest independent EAI audit: [run 40105612556](https://github.com/butnee-sys/gerchain/actions/runs/40105612556). This is automated scoped evidence, not a production certification.
- The earlier artifact from run 39849400050 carried `e872ba14c40be0904260308e626aaab8d0a4c6f7`, not the API run head `d9c8af8d7b9498ff6c814543112a06d11f73602b`; do not reuse it as evidence for d9c8af8. The later artifact on ab9799 has matching run/checkout SHA.
- The previous full-suite diagnostic intentionally unset database environment variables in its diagnostic segments; the resulting missing-DSN failures are harness/environment failures, not proof that those database paths pass. They remain non-pass evidence.

## Failure-by-failure disposition

| # | Test | Observed cause | Requirement / scope | Disposition and retest evidence |
|---:|---|---|---|---|
| 1 | `tests/test_shuud_api.py::test_full_sandbox_lifecycle_reaches_payment_release` | Operational milestone timestamps were not monotonic; validation raised `operational milestones cannot move backward in time`. | SHUUD lifecycle timing; outside EAI scope. | OPEN for SHUUD. No fix or retest claimed. |
| 2 | `tests/test_shuud_api_e2e.py::test_http_incident_to_escrow_release` | Same backwards-time validation in end-to-end lifecycle. | SHUUD incident-to-release lifecycle. | OPEN for SHUUD. No fix or retest claimed. |
| 3 | `tests/test_shuud_api_persistence_e2e.py::test_shuud_api_recovers_after_in_memory_state_loss` | Response lacked expected `incident_id`, causing KeyError. | SHUUD API persistence/recovery contract. | OPEN for SHUUD. No fix or retest claimed. |
| 4 | `tests/test_shuud_app.py::test_shuud_app_exposes_lifecycle_and_sandbox_routes` | Route introspection assumed `.path` on FastAPI `_IncludedRouter`. | SHUUD routing / framework compatibility. | OPEN for SHUUD. No fix or retest claimed. |
| 5 | `tests/test_shuud_app.py::test_shuud_app_keeps_static_mount_last` | Same unsupported `.path` assumption on `_IncludedRouter`. | SHUUD routing order. | OPEN for SHUUD. No fix or retest claimed. |
| 6 | `tests/test_shuud_dee_e2e_proof.py::test_shuud_dee_end_to_end_proves_trust_transparency_performance` | Root-of-trust rejected an unprotected DEE path. | SHUUD/DEE release protection. | OPEN for SHUUD security owner; not waived as a SHUUD release requirement. |
| 7 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs0]` | Test call omitted required `affected_vehicles` and `vehicle_value_per_minute_mnt`. | SHUUD economic-impact input validation. | OPEN for SHUUD. No fix or retest claimed. |
| 8 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs1]` | Same missing required keyword-only inputs. | SHUUD economic-impact input validation. | OPEN for SHUUD. No fix or retest claimed. |
| 9 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs2]` | Same missing required keyword-only inputs. | SHUUD economic-impact input validation. | OPEN for SHUUD. No fix or retest claimed. |
| 10 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs3]` | Test call omitted `vehicle_value_per_minute_mnt`. | SHUUD economic-impact input validation. | OPEN for SHUUD. No fix or retest claimed. |
| 11 | `tests/test_shuud_economics.py::test_economic_impact_validates_inputs[kwargs4]` | Test call omitted `affected_vehicles`. | SHUUD economic-impact input validation. | OPEN for SHUUD. No fix or retest claimed. |
| 12 | `tests/test_shuud_kpi_integrity.py::test_kpi_counts_one_canonical_snapshot_once_and_aggregates_persisted_economics` | Expected one persisted snapshot; observed count zero. | SHUUD KPI persistence/integrity. | OPEN for SHUUD. No fix or retest claimed. |
| 13 | `tests/test_shuud_kpi_integrity.py::test_updated_economic_measurement_replaces_previous_value_without_double_count` | Expected persisted snapshot/value count; observed zero. | SHUUD KPI update/idempotency. | OPEN for SHUUD. No fix or retest claimed. |
| 14 | `tests/test_shuud_measurement_api.py::test_measurement_summary_api_exposes_timing_and_economics` | Backwards-time validation prevented summary response. | SHUUD measurement API. | OPEN for SHUUD. No fix or retest claimed. |
| 15 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_combines_timing_and_economics` | Backwards-time validation prevented summary calculation. | SHUUD measurement summary. | OPEN for SHUUD. No fix or retest claimed. |
| 16 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_can_measure_timing_without_money_assumptions` | Backwards-time validation prevented timing-only summary. | SHUUD timing measurement. | OPEN for SHUUD. No fix or retest claimed. |
| 17 | `tests/test_shuud_measurement_summary.py::test_measurement_summary_requires_complete_economic_inputs` | Earlier timing validation masked the expected “must be supplied together” input error. | SHUUD economics input contract. | OPEN for SHUUD. No fix or retest claimed. |
| 18 | `tests/test_shuud_operational_timing.py::test_operational_timing_tracks_full_lifecycle_and_durations` | Operational milestones were not monotonic. | SHUUD lifecycle timing. | OPEN for SHUUD. No fix or retest claimed. |
| 19 | `tests/test_shuud_process_restart_e2e.py::test_shuud_survives_real_process_restart` | Restart test endpoint returned HTTP 404. | SHUUD process-restart/recovery contract. | OPEN for SHUUD. No fix or retest claimed. |
| 20 | `tests/test_shuud_sandbox_config.py::test_day0_rejects_invalid_window_and_threshold_order` | Test constructed `SandboxConfig` without required `status`. | SHUUD configuration validation. | OPEN for SHUUD. No fix or retest claimed. |
| 21 (historical only) | `test_shuud_workflows_are_path_isolated` | Older workflow contract expected a `paths:` filter, while the workflow used a manual trigger and disabled sandbox-smoke job. | SHUUD workflow isolation. | NOT PRESENT in latest root failure list (latest count is 20); treat as provisionally cleared only after the latest full root log confirms the test passed. No standalone pass record retained yet. |

## EAI gate failure distinct from the SHUUD diagnostic failures

The [Production Gate run 40105612580](https://github.com/butnee-sys/gerchain/actions/runs/40105612580) failed at `postgres/tests/test_canonical_schema.py::test_canonical_escrow_schema_migration_is_applied`: the test read `DATABASE_URL`, which was not set, and psycopg rejected the masked value as an invalid connection-info string. The workflow was updated to:
1. check out `github.event.pull_request.head.sha || github.sha` explicitly;
2. set `DATABASE_URL` to the isolated PostgreSQL test database;
3. apply canonical migrations 001–017 before database-backed tests and verify the version inventory.

This is a workflow correction awaiting a fresh run. It does not establish that the subsequent full suite will pass; any remaining failure must be triaged without suppressing it.

## Still-open production requirements

IAM/MFA and privileged access; legacy authority write freeze; observability and restart/recovery/no-duplicate-movement; production-like load and concurrency; backup/restore/DR with post-restore reconciliation; release governance; independently re-performed evidence; complete evidence index and authorized final approval remain OPEN unless a separate exact-SHA artifact proves closure.

**Final disposition:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`. `PASS_CANDIDATE` applies only to the listed PostgreSQL lifecycle evidence and is not a production certificate.
