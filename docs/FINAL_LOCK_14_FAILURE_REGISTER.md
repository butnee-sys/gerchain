# FINAL LOCK — 14 EAI Regression Failure Register

**Status:** OPEN — all 14 test outcomes require correction or an approved, evidence-backed disposition.
**Candidate SHA:** `e9b45aae3d8fc69997bcb21235f4f66aeb2e3565`
**Source:** PostgreSQL Production Gate run `41156406919`, artifact `13025726108`, file `segmented-tests/eai-regression.junit.xml` (1,212 tests; 10 failures; 4 errors; 18 skipped; exit code 1).
**Related broad gate:** Production Gate run `41156406965`, artifact `13025556143`; manifest says `INCOMPLETE_OR_FAILED`, source hashes complete (681/681), JUnit totals 4 failures, 1 error, 18 skipped.
**Rule:** No row may be closed solely by excluding a test from EAI scope. Each closure needs a code/test correction or a documented boundary decision, a rerun on the immutable candidate SHA, retained JUnit/log evidence, and a reviewer decision.

| # | Exact test | Observed failure | Requirement / likely correction to investigate | Status |
|---:|---|---|---|---|
| 1 | `tests.persistence.test_postgres_production_runtime::test_production_postgresql_boot_fund_lock_release_and_reconcile` | `DuplicateObject`: `gerchain_movement_amount_check` already exists during migration replay. | Migration runner must be idempotent for partially published/legacy schema history; identify exact migration statement and schema_version state before changing DDL. Preserve fail-closed checksum checks. | OPEN |
| 2 | `tests.persistence.test_postgres_production_postgres_boot::test_production_postgres_boot_and_schema_guard` | Same duplicate movement CHECK constraint. | Same migration-history/constraint reconciliation investigation; verify clean and partially migrated database paths. | OPEN |
| 3 | `tests.persistence.test_production_postgresql::test_real_postgresql_factory_and_value_truth` | Same duplicate movement CHECK constraint. | Same; prove repeated runtime factory initialization is safe without masking drift. | OPEN |
| 4 | `tests.persistence.test_production_postgresql::test_production_factory_repairs_legacy_escrow_state_constraint` | Same duplicate movement CHECK constraint. | Same; test legacy repair plus canonical movement constraints on a real PostgreSQL database. | OPEN |
| 5 | `tests.persistence.test_production_postgresql_boot::test_production_postgresql_boot_and_schema_guard` | Same duplicate movement CHECK constraint. | Same; isolate migration ordering and transaction/advisory-lock behavior. | OPEN |
| 6 | `tests.persistence.test_production_postgresql_eai::test_production_postgresql_canonical_value_flow` | Same duplicate movement CHECK constraint. | Same; canonical value-flow boot must not fail before exercising value movement. | OPEN |
| 7 | `tests.persistence.test_production_runtime_postgres::test_production_postgresql_boot_and_value_truth` | Same duplicate movement CHECK constraint. | Same; verify no existing constraint is duplicated when the migration history is incomplete or divergent. | OPEN |
| 8 | `tests.postgres.test_eai_production_runtime::test_production_factory_establishes_canonical_authority` | Fixture setup fails with the same duplicate movement CHECK constraint. | Same migration defect; retain fixture-level PostgreSQL evidence after correction. | OPEN |
| 9 | `tests.postgres.test_eai_production_runtime::test_postgresql_canonical_fund_lock_release_proof` | Fixture setup fails with the same duplicate movement CHECK constraint. | Same migration defect; re-run actual fund/lock/release proof after boot succeeds. | OPEN |
| 10 | `tests.production.test_production_runtime_postgres_smoke::test_production_factory_executes_refund_cancel_and_settlement_on_real_postgresql` | Fixture setup timed out after 300 seconds. | Inspect PostgreSQL lock waits, concurrent DDL/metadata creation, TRUNCATE/isolation fixture ordering, and connection cleanup. Do not merely increase timeout. | OPEN |
| 11 | `tests.production.test_runtime_postgres_smoke::test_production_runtime_factory_boots_against_postgres` | Same 300-second setup timeout. | Same lock/fixture investigation; prove bounded startup and independent test isolation. | OPEN |
| 12 | `tests.test_final_lock_contract::test_core_gate_excludes_shuud_product_tests_but_keeps_boundary_tests` | Workflow omits explicit SHUUD boundary-test exceptions required by the contract test. | Preserve SHUUD as a separate product while retaining the required boundary contract tests in EAI/core CI; update workflow and/or test only with architecture-consistent rationale. | OPEN |
| 13 | `tests.test_production_postgres::test_production_postgres_full_value_flow` | `sqlalchemy.exc.NoResultFound` while looking up the expected value-flow record. | Trace transaction/escrow state transition, persisted movement identity and query predicates; prove the expected release/value record is durably written and queryable. | OPEN |
| 14 | `tests.test_production_postgres_boot::test_production_runtime_boots_on_postgresql` | Test asserts migration version 12; actual canonical schema_version is 17. | Update stale assertion to the canonical migration inventory only after verifying all 17 checksums and applied history; do not change expected version to 17 without that proof. | OPEN |

## Cross-artifact SHA and evidence findings

- The Production Gate manifest binds `canonical_commit_sha`, `commit_sha`, and `checked_out_head_sha` to the candidate SHA; `source_hashes_complete=true`, `source_file_count=681`, and `missing_source_files=[]`.
- Its `github_event_sha` is `2119a69a02e65b482b2939a3681bcc3dcb0a0e73`, the PR merge/event SHA, not the tested PR-head SHA. This is recorded separately; it must not be mistaken for the checked-out candidate SHA.
- Production Gate manifest result is `INCOMPLETE_OR_FAILED`, with 313 JUnit files, 4 failures, 1 error and 18 skipped; seven gate file failures are recorded. Complete source hashes do not convert failed tests into a pass.
- PostgreSQL Production Gate segmented regression JUnit reports 1,212 tests, 10 failures, 4 errors, 18 skipped. The 14 rows above are the exact 14 failure/error cases from that report.
- The same run's separate product-scope list excludes SHUUD/SANDBOX product files from EAI regression. This is not a disposition of the historical 21 SHUUD failures; those remain tracked in `docs/FINAL_LOCK_21_FAILURE_REGISTER.md`.
- The latest independent audit run `41156406897` is successful for its defined EAI-only scope. It does not close the 14 failures, the 21 historical SHUUD failures, or the production operational controls.

## Priority order

1. Resolve duplicate movement constraint replay with migration-history and database-catalog evidence.
2. Resolve PostgreSQL smoke fixture timeouts using lock-wait and connection diagnostics.
3. Resolve the value-flow missing-record failure with persisted transaction-level evidence.
4. Correct the core workflow boundary-test selection and stale migration-version assertion.
5. Re-run the complete relevant regression and all production gates on one immutable SHA; regenerate and validate every artifact against that SHA.

**Decision remains:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`. No item above is waived or marked fixed.
