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


## Audit addendum — 2026-10-24 (candidate `a8fd6092ace34dcd63a763f505af9be93d549574`)

This addendum records direct inspection of GitHub Actions run metadata and job logs. It does not close any prior blocker.

### Exact-SHA run inventory

The following runs completed at candidate SHA `a8fd6092ace34dcd63a763f505af9be93d549574`:

- [PostgreSQL Production Gate, run 40046489334](https://github.com/butnee-sys/gerchain/actions/runs/40046489334): workflow conclusion `success`; its only job `postgres-production-gate` concluded `success`.
- [Production Gate, run 40046489274](https://github.com/butnee-sys/gerchain/actions/runs/40046489274): workflow/job conclusion `success`, but the job log shows `python -m pytest --maxfail=1 --disable-warnings -v` failed immediately with `No module named pytest`; the shell command then executed `|| echo "Tests completed with failures, check logs."` and therefore did not fail the job. **This is not a passing full-suite result.**
- [CI Test Suite, run 40046489330](https://github.com/butnee-sys/gerchain/actions/runs/40046489330): selected suite passed `43 passed in 1.12s`. The logged command lists six selected test files; it is not evidence that the full repository suite passed.
- [Independent Production Audit, run 40046489318](https://github.com/butnee-sys/gerchain/actions/runs/40046489318): `clean-postgres-audit` concluded `success`. This is useful scoped evidence, but it does not by itself prove independent re-performance of every MG-02–MG-14 requirement.
- [PostgreSQL Migration and Production Proof, run 40046489304](https://github.com/butnee-sys/gerchain/actions/runs/40046489304): `postgres-proof` concluded `success`.
- [PostgreSQL production migration gate, run 40046489307](https://github.com/butnee-sys/gerchain/actions/runs/40046489307): `postgres-migration-gate` concluded `success`.
- [core-gates, run 40046489314](https://github.com/butnee-sys/gerchain/actions/runs/40046489314): `cancelled`; no jobs were returned by the jobs endpoint.

### Artifact availability and claims

The GitHub Actions artifacts endpoint for run `40046489334` returned an empty artifact list at the time of this inspection. Therefore this inspection could not independently re-open the claimed JSON, its `.sha256` companion, the 13-source hash inventory, the migration-history report, or the six-test JUnit XML from that run. The supplied report of `PASS_CANDIDATE`, matching SHA fields, 13/13 source hashes, 17/17 migration checksums and 6/6 JUnit tests is recorded as **reported evidence, not independently re-verified in this audit pass** until a downloadable retained artifact and its exact hashes are available.

### Failure-count and scope disposition

The 21-test diagnostic list above remains the baseline inventory from run `39849400091`; later user-provided notes report 20 remaining failures after removing the workflow-isolation test from the list. This audit has not retrieved a new downloadable JUnit/diagnostic artifact proving the current count or that the remaining 20 are fixed. The 20 SHUUD/SANDBOX tests remain **OPEN** for correction or an independently reviewed scope decision. A claim that they are outside the EAI gate does not erase their failure or prove they are irrelevant to the repository's release policy.

### Current source revision

At the time of this update, PR #111 head is `12ddfb35a0eda9dce3e025968a38cc481c145d2c`, a documentation-only update after the inspected candidate. All evidence above is bound to `a8fd6092ace34dcd63a763f505af9be93d549574`, not to the newer head unless rerun or explicitly proven invariant. Do not combine these results into one exact-SHA pass claim.

### Required next proof

1. Preserve a downloadable artifact for the chosen immutable release candidate, including the JSON report, JSON SHA-256 file, source-hash inventory, migration history/checksums, PostgreSQL constraint report, and JUnit XML.
2. Correct the Production Gate workflow so a missing test dependency or pytest failure fails the job rather than being swallowed by `|| echo`; install the required test dependencies in that job.
3. Rerun the full repository suite and produce a per-test result artifact; resolve or formally disposition every remaining failure with reviewer and scope evidence.
4. Re-run all required PostgreSQL, migration, re-performance, and independent-audit gates on one exact candidate SHA.
5. Close the remaining security/operations/DR/performance/release-governance requirements and obtain explicit authorized approval.

**Disposition remains: FINAL LOCK = OPEN; PRODUCTION READY = NOT VERIFIED.**


## Audit addendum — 2026-10-24 (candidate `a1056e176ffefd8b78f552594dff5fdb39c4a401`)

This addendum supersedes no earlier evidence; it records a newer candidate and keeps results bound to their own SHA.

### Current exact-SHA run results

- [Production Gate run 40102667162](https://github.com/butnee-sys/gerchain/actions/runs/40102667162): **FAILURE** at SHA `a1056e176ffefd8b78f552594dff5fdb39c4a401`. Job log: 1,318 tests collected; first test `postgres/tests/test_canonical_eai_postgres.py::test_canonical_postgres_transaction_and_deep_truth` failed because `GERCHAIN_POSTGRES_DSN` was not set. The job stopped at `--maxfail=1`; this run does not establish the current 21-failure count or pass the full suite.
- [PostgreSQL Production Re-performance run 40102667219](https://github.com/butnee-sys/gerchain/actions/runs/40102667219): **SUCCESS** at the same SHA. Downloaded artifact ID `12563138670`, `production-gate-evidence-a1056e.zip`, inspected directly. `migration-catalog-proof.json`, `production-gate-evidence.json`, and `reconciliation-report.json` all bind to `a1056e176ffefd8b78f552594dff5fdb39c4a401`. PostgreSQL 16.15, 17 migration files, migration-history versions 1–17, checksums, and escrow constraint catalog records were present. Evidence reports `sha_match: true`, boot status PASS, and reconciliation `matched: true`.
- Important limitation: reconciliation explicitly describes a **fresh empty baseline**: zero movements, witnesses, outbox rows, idempotency rows, and escrows. It does not prove a non-empty end-to-end production transaction graph.
- The artifact still embeds migration history and escrow constraints inside `migration-catalog-proof.json`; standalone `migration-history.json` and `postgres-constraints.json` are absent. Treat this as an evidence-packaging gap until the workflow emits and retains both standalone files.
- [FINAL EAI/CORE Exact-SHA Gate run 40102667163](https://github.com/butnee-sys/gerchain/actions/runs/40102667163), [EAI PostgreSQL Re-performance run 40102667164](https://github.com/butnee-sys/gerchain/actions/runs/40102667164), [Independent Production Audit run 40102667185](https://github.com/butnee-sys/gerchain/actions/runs/40102667185), [PostgreSQL Production Gate run 40102667244](https://github.com/butnee-sys/gerchain/actions/runs/40102667244), [Production Readiness Gates run 40102667174](https://github.com/butnee-sys/gerchain/actions/runs/40102667174), and [CI Test Suite run 40102667188](https://github.com/butnee-sys/gerchain/actions/runs/40102667188) reported workflow success at this SHA. These are scoped gate results, not a substitute for the failed Production Gate or the remaining operations/security evidence.
- [core-gates run 40102667181](https://github.com/butnee-sys/gerchain/actions/runs/40102667181) was pending at inspection; no pass is inferred.
- The older artifact from run 39849400050 that embedded SHA `e872ba14c40be0904260308e626aaab8d0a4c6f7` while the previously inspected run context expected `d9c8af8d7b9498ff6c814543112a06d11f73602b` remains a historical SHA mismatch. Do not use it as evidence for either candidate. The new `a1056e...` artifact is correctly bound to its own SHA; this does not retroactively repair the older artifact.

### Status of the 21-test register

The 21 entries above are from the retained diagnostic at SHA `d9c8af8d7b9498ff6c814543112a06d11f73602b`. They remain individually **OPEN**: no subsequent full-suite JUnit or per-test rerun artifact was inspected proving each fixed or formally waived. The current Production Gate stopped at its first missing-DSN failure, so it cannot resolve any of those 21 entries.

### Immediate corrective actions

1. Fix the Production Gate's PostgreSQL test environment so the first test receives a disposable PostgreSQL 16 DSN, then rerun. Do not suppress the missing-DSN error or skip the test.
2. Emit `migration-history.json` and `postgres-constraints.json` as standalone files from the live database queries and include them in the retained artifact.
3. Generate a fresh full-suite JUnit/diagnostic artifact and update each of the 21 rows only with a fix commit or reviewer-approved scope decision plus passing evidence.
4. Run Production Gate, core-gates, exact-SHA gate and independent audit on one immutable candidate SHA, then verify all artifact manifests and file hashes match it.
5. Continue to require independent evidence for IAM/MFA, privileged access, authority-store write freeze, observability/recovery, backup/restore/DR, production-like performance/concurrency, release governance and authorized approval.

**Current decision remains: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.**


## Audit addendum — 2026-10-25 (candidate `b193bb379d45a4c012a4d652ab23972f39adace8`)

This addendum records the latest exact-SHA workflow results inspected after the earlier `d9c8af8...` candidate. It does not close any failure or authorize a production release.

### Current candidate and workflow outcomes

Candidate SHA: `b193bb379d45a4c012a4d652ab23972f39adace8`.

- [Production Gate, run 40110638161](https://github.com/butnee-sys/gerchain/actions/runs/40110638161): **FAILURE**. The job applied migrations 1–17 successfully, then failed at `postgres/tests/test_canonical_schema.py::test_canonical_escrow_schema_migration_is_applied`. Psycopg reported `ProgrammingError: missing "=" after "***127.0.0.1:5432/gerchain_test" in connection info string`. The log redacts the connection string; inspect the actual variable source and normalize the DSN by driver (native `postgresql://` for `psycopg.connect`; SQLAlchemy `postgresql+psycopg://` only for SQLAlchemy). Do not infer a pass from the workflow's migration pre-step.
- [Production PostgreSQL Gate, run 40110638150](https://github.com/butnee-sys/gerchain/actions/runs/40110638150): **FAILURE**. PostgreSQL logs contain repeated `constraint "gerchain_movement_amount_check" ... already exists`, authentication failures for `gerchain`, and duplicate-key violations for `uq_gerchain_release_idempotency_key`. These are blockers requiring identification of the invoking tests and whether schema repair/bootstrap is racing or being invoked repeatedly; expected negative-test errors must be distinguished from unhandled failures by JUnit and assertions.
- [FINAL EAI/CORE Exact-SHA Gate, run 40110638291](https://github.com/butnee-sys/gerchain/actions/runs/40110638291): workflow conclusion `success`; inspect its retained artifact before treating it as proof beyond the specific gate.
- [PostgreSQL Production Re-performance, run 40110638237](https://github.com/butnee-sys/gerchain/actions/runs/40110638237): workflow conclusion `success`; inspect report/JUnit and SHA binding before acceptance.
- [Independent Production Audit, run 40110638200](https://github.com/butnee-sys/gerchain/actions/runs/40110638200): workflow conclusion `success`; this is scoped automated audit evidence, not by itself a sign-off for every operational requirement.
- [core-gates, run 40110638176](https://github.com/butnee-sys/gerchain/actions/runs/40110638176): still `pending` at the time of this audit; no final outcome is recorded here.

### Additional errors to track

The earlier production and core gate logs also contain PostgreSQL `integer out of range` errors during test execution. They must be mapped to the exact test/query and column type before changing schema or bounds. The `ledger_transfer()` argument mismatch mentioned in the work notes must likewise be tied to its exact failing test and function signature; this addendum does not claim it is fixed because a verified log excerpt and passing retest were not available in the inspected latest run.

### Required remediation sequence

1. Fix the connection-string source for each driver and add a small preflight that verifies the scheme/driver contract without printing credentials. Re-run the failing schema test and the complete Production Gate.
2. Trace duplicate-constraint creation to its migration/bootstrap/repair call sites; make schema creation/repair safe under repeated and concurrent startup, then prove this on a fresh PostgreSQL 16 database with concurrent runners and a second no-op run.
3. For every `integer out of range`, record test name, SQL statement/parameter, affected column/type, intended numeric domain, and the approved schema/application correction. Do not widen numeric types blindly.
4. Record the exact `ledger_transfer()` caller, expected signature, argument types/order, and regression test. Preserve atomicity, idempotency, and no-duplicate-movement invariants.
5. Re-run all applicable tests and retain JUnit, PostgreSQL logs, migration history, constraint catalog, source hashes, and report SHA-256 from one immutable commit. Compare the current 21-row register with the new full-suite results; do not mark a row resolved without its passing retest or a reviewer-approved scope rationale.
6. Bind independent re-performance and the remaining IAM/MFA, privileged access, monitoring/recovery, performance/concurrency, backup/restore/DR, release-governance and authorized human approval evidence to that same candidate SHA.

**Decision remains unchanged:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`. No evidence in this addendum grants final lock.


## Follow-up findings — candidate `4cd8337f61a5a358daa6370ec3428e8cac703685`

The prior 21 root-suite failures remain **OPEN**; the rows above are not resolved by this follow-up. Newer exact-SHA runs exposed additional migration/test-environment defects:

| Test / gate | Observed evidence | Requirement area | Corrective action in this commit | Verification still required |
|---|---|---|---|---|
| `postgres/tests/test_canonical_schema.py::test_canonical_escrow_schema_migration_is_applied` | Test points the canonical runner at `postgres/schema`, a historical alias directory with multiple version-002 files; runner correctly fails closed with an ambiguous version. | Canonical migration source and schema contract | Point test at `postgres/migrations`; assert the canonical state constraint and versions 1–17. | Re-run the test and the full PostgreSQL gate on the new commit. |
| `tests/postgres/test_migration_gate_postgresql.py::test_postgresql_clean_migration_rerun_and_checksum_drift_are_safe` | Psycopg receives a SQLAlchemy `postgresql+psycopg://` URL; migration test also expected only versions 1–16 although the canonical chain contains 17. | Migration test correctness / DSN handling | Normalize the URL for psycopg and align the test with versions 1–17. | Re-run isolated migration, idempotency and checksum-drift tests. |
| `tests/postgres/test_migration_race.py` | Both real-PostgreSQL race tests fail before exercising concurrency because psycopg cannot parse the SQLAlchemy dialect URL. | Migration concurrency / fail-closed checksum handling | Normalize the DSN before opening psycopg connections. | Re-run both race tests on PostgreSQL 16. |
| `tests/postgres/test_production_postgres_reperformance.py` (3 tests) | Lifecycle JUnit reported 3 failures because the runtime migration chain attempted to add `gerchain_movement_amount_check` to a database already containing that constraint but lacking the canonical migration history expected by the test. | Canonical migration source, migration history and PostgreSQL constraint consistency | Initialize the diagnostic database with the canonical 17-migration chain before database-backed diagnostics; run lifecycle re-performance against the separately migrated `gerchain_migration_chain`; export constraint evidence from that same database. No historical migration file checksum is changed. | Confirm migration history, constraint catalogue, lifecycle JUnit (0 failures/errors), and report SHA all match the new checked-out HEAD. |

The latest observed run at the candidate SHA also had the full Production Gate fail in `postgres/tests/test_canonical_schema.py`; the PostgreSQL lifecycle artifact reported `evidence_status=INCOMPLETE_OR_FAILED` with 3 JUnit failures. These are not passing evidence. The changes above are corrective hypotheses grounded in those logs; they are **not considered resolved until the new commit runs and retained artifacts confirm them**.

Decision remains: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.


## Audit addendum — candidate `1f2542bf50da3831d98f298b5a8544b7ae989906`

### Verified PostgreSQL evidence

- [Production PostgreSQL Gate run 40144870154](https://github.com/butnee-sys/gerchain/actions/runs/40144870154) completed `success` at this exact SHA. Retained artifact `12580161268` contains `migration-lifecycle-report.json`, `migration-history.json`, `postgres-constraints.json`, sidecar SHA-256 files and JUnit XML.
- `migration-lifecycle-report.json`: `evidence_status=PASS_CANDIDATE`; `commit_sha=checked_out_head_sha=1f2542bf50da3831d98f298b5a8544b7ae989906`; `sha_match=true`; source hashes 13/13 complete; migration files/applied versions 17/17; checksums match; JUnit 6 tests, 0 failures, 0 errors, 0 skipped. Recomputed report SHA-256 `9b0d8ee8602402b9740a2898970bf57c56699376458426e1fb8efeb9cb9e8cc9` matches its `.sha256` sidecar.
- `migration-history.json` SHA-256 `beb97ae4ba6ee670e1ff81cb6ad90b05531121e4ff05beaf79f9afb1bb38380e`; it lists versions 1–17 and binds to the same SHA.
- `postgres-constraints.json` SHA-256 `0a61586674f4d43930762cc9b278f8c8454903561022777f68fa45dbfea8851c`; it describes `gerchain_migration_chain`, 36 constraints, all reported validated, and binds to the same SHA.
- [PostgreSQL migration gate run 40144870110](https://github.com/butnee-sys/gerchain/actions/runs/40144870110), [PostgreSQL production migration gate run 40144870112](https://github.com/butnee-sys/gerchain/actions/runs/40144870112), [PostgreSQL concurrency and migration gate run 40144870120](https://github.com/butnee-sys/gerchain/actions/runs/40144870120), [PostgreSQL Production Re-performance run 40144870127](https://github.com/butnee-sys/gerchain/actions/runs/40144870127), [FINAL EAI/CORE Exact-SHA Gate run 40144870150](https://github.com/butnee-sys/gerchain/actions/runs/40144870150), and [Independent Production Audit run 40144870170](https://github.com/butnee-sys/gerchain/actions/runs/40144870170) reported success at the same SHA. These scoped passes do not establish full-suite or operational readiness.

### Remaining failures observed on this candidate

- [Production Gate run 40144870182](https://github.com/butnee-sys/gerchain/actions/runs/40144870182) failed after 23 passed tests at `postgres/tests/test_production_runtime.py::test_production_runtime_canonical_value_flow_and_reconciliation`: `NoResultFound` because the fixture deleted all `LedgerAccountModel` rows and did not recreate the escrow ledger account required by the FUND transfer. This commit adds the missing escrow ledger account to the test fixture; the failure remains unclosed until the rerun passes.
- The retained segmented diagnostics in artifact `12580161268` reported 29 root failures: the 20 previously recorded SHUUD/SANDBOX failures remain open, plus 9 PostgreSQL-backed runtime tests failing with duplicate `gerchain_movement_amount_check` constraints. These duplicate-constraint failures arose after setup/settlement tests and indicate shared-database state contamination in the diagnostic workflow; the clean-database reset is moved after setup tests and before segmented diagnostics in this commit.
- Additional segment failures in the same artifact: persistence 9 failed; PostgreSQL tests 5 failed and 2 errors; production tests 15 failed; PostgreSQL migration tests 5 failed; services 8 failed. They include SQLAlchemy URL passed to psycopg, one positional argument mismatch in `PostgreSQLAtomicLedger.transfer_in_transaction`, PostgreSQL authentication failure for `gerchain`, SQLite-incompatible schema inspection SQL, constraint-definition expectation mismatch (`>=0` versus `>=`), and a self-repair source-template mismatch. The failure names and tracebacks remain in the retained artifact logs; none are waived by this addendum.
- The migration-gate diagnostic still had `assert 17 == 16`; this was a stale assertion after the earlier version-range update. This commit corrects the distinct-version count to 17. The separate PostgreSQL migration gate success does not by itself prove this diagnostic assertion passed.

The above are follow-up findings and fixes, not blanket resolution. New exact-SHA runs must prove the fixture fix, clean database isolation, migration count, per-segment outcomes and artifact provenance. The original 21-failure register remains individually OPEN pending passing retests or reviewer-approved scope decisions.

**Decision remains: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.**


## Follow-up — candidate `1b099a88770609c6e34f5a945d15a18975ed473c`

- [Production Gate run 40145446599](https://github.com/butnee-sys/gerchain/actions/runs/40145446599) failed after 37 passing tests at `tests/core/test_concurrent_operations.py::test_disjoint_resources_run_concurrently_and_results_keep_input_order` with `NameError: name 'next_index' is not defined` in `core/concurrent_operations.py`.
- Code inspection found both an undefined variable and a scheduler ordering gap: a later pending operation could overtake an earlier pending operation sharing one resource when the earlier item was blocked by a different active resource. This commit initializes the scan index and tracks blocked resources to preserve submission order for overlapping resource keys; a regression test covers the cross-resource case.
- This new concurrency correction is not considered passed until the exact-SHA full Production Gate and concurrency-specific tests complete successfully.

Decision remains `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.

## Follow-up — candidate `e3d1542c49a224f08d1efe1b23d8acef0e306151`

- [Production Gate run 40145731681](https://github.com/butnee-sys/gerchain/actions/runs/40145731681) failed at `tests/integration/test_postgresql_production_reperformance.py::test_postgresql_canonical_value_flow_is_atomic_and_reconciled` with SQLAlchemy `NoResultFound`. The fixture created sender/beneficiary/settlement accounts but omitted canonical ledger accounts for `esc-release`, `esc-refund`, and `esc-cancel`, although FUND transfers value into each escrow account before subsequent state transitions.
- This commit seeds the three zero-balance escrow ledger accounts explicitly. This is a fixture correction for a real ledger precondition, not a waiver; rerun the exact-SHA Production Gate and deep reconciliation before closing this item.

Decision remains `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.

## Follow-up — candidate `b52d7079eed7d61287bc35969687fffc28f547d9`

- [Production Gate run 40146252902](https://github.com/butnee-sys/gerchain/actions/runs/40146252902) passed the previous PostgreSQL escrow-account seeding issue and failed at `tests/integration/test_production_postgres_runtime.py::test_production_postgresql_canonical_value_flow`: observed `alice` balance 70 while the test expected 50. The REFUND path returns the 20-unit escrow funding to Alice, so the correct net balance is 100 − 30 release = 70; the assertion is corrected accordingly.
- This balance correction is based on the implemented fund/refund flow and does not weaken deep reconciliation. The exact-SHA Production Gate must pass after the correction.

Decision remains `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.

## Follow-up — candidate `c88f8202587524acb0c40dc582c5760f0bf2a754`

- [Production Gate run 40146423455](https://github.com/butnee-sys/gerchain/actions/runs/40146423455) failed at `tests/integration/test_production_postgres_value_flow.py::test_production_postgres_value_flow_and_deep_reconciliation` with `AttributeError: 'dict' object has no attribute 'transaction_status'`. The test helper passed a SQLAlchemy `Connection` (already inside `engine.begin()`) to a migration runner that requires an idle psycopg connection, and pointed it at the historical `postgres/schema` alias directory rather than the canonical migration source.
- This commit changes the helper to use a native psycopg DSN, an idle psycopg connection, and `postgres/migrations`. The migration-source/connection fix must pass on the new SHA before this finding can be closed.

Decision remains `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.

## Audit addendum — 2026-10-25 (decision freshness and artifact SHA provenance)

This addendum records workflow defects found while investigating the stale `LOCKED` decision and the re-performance artifact SHA mismatch. It does not close any production gate.

### Findings

1. **Old `LOCKED` decision is historical, not evidence for a new candidate.** The repository's tracked `artifacts/master_v1/master_certificate.json` explicitly records `HISTORICAL_EVIDENCE_ONLY`, `final_lock_granted: false`, target SHA `10a408dc4a7821db85a9bc68cfccdb66a20b4dcf`, and historical run ID `39799640206`. It must not be reused as a current release decision. Any downloaded artifact reporting `decision: LOCKED` for that old target is invalid for the current candidate.

2. **Master-gate controller argument mismatch.** `.github/workflows/production-master-gate.yml` invoked the controller with `--expected-sha`, but `scripts/production_gate_controller.py` defines `--expected-source-sha`. This could prevent fresh decision generation. Commit `2461cb115bcc9e831405b1747d89057f3bab852a` corrects the argument, removes a pre-existing decision file before recomputation, and forces `NOT_LOCKED` when the fresh decision's source or checked-out SHA differs from the target. This is a source-level correction only; it still needs a workflow run and artifact verification.

3. **Re-performance artifact name used a different SHA expression from checkout.** `.github/workflows/ea35-postgres-reperformance.yml` checked out `${{ github.event.pull_request.head.sha || github.sha }}` but named its artifact with `${{ github.sha }}`. On pull-request events, `github.sha` may identify the synthetic merge commit while checkout/manifest identify the PR head. Commit `da17ed4e4a9ece2ceeaaef5592141a7371501cd0` aligns the artifact name with the checked-out PR-head SHA expression. This addresses one provenance ambiguity; it does not prove that the previously mismatched artifact was regenerated or repaired.

### Verification still required

- Run the corrected master-gate workflow from a fresh checkout; verify no pre-existing decision is reused and the emitted decision JSON's `source_commit_sha`, `checked_out_head_sha`, expected target SHA, run ID and attempt agree.
- Run the corrected re-performance workflow; inspect the downloadable artifact and confirm the artifact name, internal manifest, `tested-commit.txt`, source hashes, migration history, JUnit and workflow API head all refer to the same SHA. Reject any merge-SHA/head-SHA discrepancy.
- Retrieve and inspect the final Production Gate and `core-gates` logs/JUnit. Previous attempts at `d9c8af8d7b9498ff6c814543112a06d11f73602b` were cancelled; they do not provide a completed full-suite verdict.
- The 21 failures in the register remain individually OPEN. No test was marked fixed, waived or out of scope by the workflow corrections above.
- IAM/MFA, privileged access, legacy authority write-freeze, observability/recovery, production-like performance/concurrency, backup/restore/DR, release governance, independent re-performance, complete evidence index and authorized approval remain outstanding.

**Decision remains: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.**


## Follow-up — 2026-10-25: PostgreSQL re-performance workflow did not create a job

The new run [PostgreSQL Production Re-performance, run 40204082279](https://github.com/butnee-sys/gerchain/actions/runs/40204082279) at SHA `819a1c734f4847168a65187e2f043e626c51840b` concluded failure and the Actions jobs endpoint returned zero jobs. Inspecting `.github/workflows/postgres-production-reperformance.yml` identified a duplicate `with:` block under the shell-based “Assert checkout matches the tested PR head” step. A `run:` step cannot take an action `with:` input; this made the workflow invalid before any test evidence could be collected.

Commit `0b8a3d177a9128a0b7a87a6c4c76c46aab30acc7` removes the invalid duplicate block and updates the migration evidence step label to reflect 17 migrations. This is a workflow syntax correction only. It remains OPEN until a new run has a real job, the checkout SHA assertion passes, the artifact is retained, and its internal `tested-commit.txt`, manifest SHA, migration inventory, constraints and JUnit agree with the workflow head SHA.

The previous exact-SHA artifact mismatch remains rejected. The 21 root-suite failures and all separately recorded segmented failures remain unresolved unless new passing logs or a reviewed scope disposition explicitly closes each item.

**Decision remains: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.**
