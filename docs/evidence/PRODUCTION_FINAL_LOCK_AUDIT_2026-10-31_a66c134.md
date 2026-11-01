# Production Final-Lock Evidence Audit — 2026-10-31

**Decision:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.
**Inspected branch candidate:** `a66c134e7706cb8a95898a98a99156fe92dbedba`.
**Previous candidate requiring separate tracking:** `d9c8af8d7b9498ff6c814543112a06d11f73602b`.

This record is an evidence audit, not a certificate or a waiver. No test is marked resolved.

## 1. Run inventory at candidate a66c134

| Gate | Run | Result | Evidence / limitation |
|---|---:|---|---|
| Production Gate | [41160843728](https://github.com/butnee-sys/gerchain/actions/runs/41160843728) | **FAILURE** | Job `124417813073`; artifact `13027127149`; manifest `INCOMPLETE_OR_FAILED`. |
| Production PostgreSQL Gate | [41160843744](https://github.com/butnee-sys/gerchain/actions/runs/41160843744) | **FAILURE** | Job `124417813149`; artifact `13027915368`; retained segmented JUnit/log. |
| core-gates | [41160843643](https://github.com/butnee-sys/gerchain/actions/runs/41160843643) | **IN_PROGRESS at inspection** | No completed result or artifact available at inspection. |
| Independent Production Audit | [41160843737](https://github.com/butnee-sys/gerchain/actions/runs/41160843737) | SUCCESS | Scoped audit only; does not close broad regressions or operational controls. |
| PostgreSQL Production Re-performance | [41160843663](https://github.com/butnee-sys/gerchain/actions/runs/41160843663) | SUCCESS | Scoped run; must be checked against its retained artifact and exact SHA before use. |
| EAI PostgreSQL Re-performance | [41160843642](https://github.com/butnee-sys/gerchain/actions/runs/41160843642) | SUCCESS | Scoped run; does not resolve unrelated suite failures. |
| FINAL EAI/CORE Exact-SHA Gate | [41160843644](https://github.com/butnee-sys/gerchain/actions/runs/41160843644) | SUCCESS | Exact-SHA gate only; not a production readiness approval. |
| PostgreSQL concurrency and migration gate | [41160843908](https://github.com/butnee-sys/gerchain/actions/runs/41160843908) | SUCCESS | Scoped migration/concurrency evidence only. |
| PostgreSQL Migration and Production Proof | [41160843863](https://github.com/butnee-sys/gerchain/actions/runs/41160843863) | SUCCESS | Scoped proof; not a substitute for failed production gate. |
| CI Test Suite | [41160843768](https://github.com/butnee-sys/gerchain/actions/runs/41160843768) | SUCCESS | Selected CI suite only; not the complete production regression suite. |

All listed runs were associated with candidate SHA `a66c134e7706cb8a95898a98a99156fe92dbedba`. The Production Gate manifest separately records `github_event_sha=58a1771f1923d1f4525b306b76d0718b974dfe00` (PR merge/event SHA); this is not the tested candidate SHA.

## 2. Production Gate artifact review

Artifact: [13027127149](https://github.com/butnee-sys/gerchain/actions/runs/41160843728/artifacts/13027127149)
ZIP SHA-256: `4c0b9b87970e189468d8dc8e542a4e85f8e8730889525fee713497ee6834cb07`.

Observed in `canonical-evidence-manifest.json`:

- `canonical_commit_sha`, `commit_sha`, `checked_out_head_sha`, and `pull_request_head_sha` all equal `a66c134e7706cb8a95898a98a99156fe92dbedba`.
- `source_hashes_complete=true`; 681 source files hashed; `missing_source_files=[]`.
- `evidence_status=INCOMPLETE_OR_FAILED`.
- `gate_file_failure_count=7`.
- JUnit inventory: 313 files; totals: 4 failures, 1 error, 18 skipped.

Therefore the complete source-hash inventory does **not** make this artifact a passing candidate. Its own manifest is failed/incomplete.

The five failure/error node IDs retained in the broad Production Gate JUnit bundle are:

1. `tests.production.test_production_runtime_postgres_smoke::test_production_factory_executes_refund_cancel_and_settlement_on_real_postgresql` — setup timeout (>300s).
2. `tests.production.test_runtime_postgres_smoke::test_production_runtime_factory_boots_against_postgres` — `TypeError: 'NoneType' object is not subscriptable`.
3. `tests.test_final_lock_contract::test_core_gate_excludes_shuud_product_tests_but_keeps_boundary_tests` — workflow does not contain the boundary-test exclusion contract expected by the test.
4. `tests.test_production_postgres::test_production_postgres_full_value_flow` — `sqlalchemy.exc.NoResultFound`; expected value-flow record not found.
5. `tests.test_production_postgres_boot::test_production_runtime_boots_on_postgresql` — stale assertion `17 == 12`.

The manifest reports seven gate-file failures, so the five JUnit node IDs above are not a complete explanation of every gate-file failure. The remaining two must be resolved from the per-file logs and gate manifest before any closure.

## 3. Production PostgreSQL regression — exact JUnit nodes

Artifact: [13027915368](https://github.com/butnee-sys/gerchain/actions/runs/41160843744/artifacts/13027915368)
ZIP SHA-256: `f1ecc3dc8e2928be8bcf838ac6179372ef5c300de7f8f1469540cc8a40206c73`.

The retained `segmented-tests/eai-regression.junit.xml` reports **1,212 tests, 10 failures, 4 errors, 18 skipped** (14 failed/error node IDs). All 14 remain OPEN:

| # | Exact JUnit node ID | Observed reason | Requirement area / evidence needed |
|---:|---|---|---|
| 1 | `tests.persistence.test_postgres_production_runtime::test_production_postgresql_boot_fund_lock_release_and_reconcile` | Duplicate CHECK constraint `gerchain_movement_amount_check` | Migration/runtime schema initialization must reconcile existing constraint without masking drift; prove clean and legacy/replay paths. |
| 2 | `tests.persistence.test_production_postgres_boot::test_production_postgres_boot_and_schema_guard` | Same DuplicateObject constraint | Same; preserve schema guard and migration integrity. |
| 3 | `tests.persistence.test_production_postgresql::test_real_postgresql_factory_and_value_truth` | Same DuplicateObject constraint | Runtime factory idempotent initialization and value-truth proof. |
| 4 | `tests.persistence.test_production_postgresql::test_production_factory_repairs_legacy_escrow_state_constraint` | Same DuplicateObject constraint | Legacy escrow repair plus movement-constraint validation. |
| 5 | `tests.persistence.test_production_postgresql_boot::test_production_postgresql_boot_and_schema_guard` | Same DuplicateObject constraint | Migration ordering/history and schema guard. |
| 6 | `tests.persistence.test_production_postgresql_eai::test_production_postgresql_canonical_value_flow` | Same DuplicateObject constraint | Canonical value-flow boot and durable movement proof. |
| 7 | `tests.persistence.test_production_runtime_postgres::test_production_postgresql_boot_and_value_truth` | Same DuplicateObject constraint | Runtime boot and reconciliation on PostgreSQL. |
| 8 | `tests.postgres.test_eai_production_runtime::test_production_factory_establishes_canonical_authority` | Fixture setup fails on same DuplicateObject constraint | Canonical authority initialization after a valid production boot. |
| 9 | `tests.postgres.test_eai_production_runtime::test_postgresql_canonical_fund_lock_release_proof` | Fixture setup fails on same DuplicateObject constraint | Real PostgreSQL fund/lock/release proof. |
| 10 | `tests.production.test_production_runtime_postgres_smoke::test_production_factory_executes_refund_cancel_and_settlement_on_real_postgresql` | Fixture setup timeout (>300s) | Inspect lock waits, fixture DDL/isolation and connection cleanup; do not merely extend timeout. |
| 11 | `tests.production.test_runtime_postgres_smoke::test_production_runtime_factory_boots_against_postgres` | Fixture setup timeout (>300s) | Same lock/fixture diagnosis and bounded startup proof. |
| 12 | `tests.test_final_lock_contract::test_core_gate_excludes_shuud_product_tests_but_keeps_boundary_tests` | Expected `! -name 'test_shuud_boundary.py'` missing from workflow | Align CI boundary selection with canonical architecture; retain boundary contract tests. |
| 13 | `tests.test_production_postgres::test_production_postgres_full_value_flow` | `NoResultFound` | Trace transaction, escrow, release and persisted movement identifiers; prove record durability and queryability. |
| 14 | `tests.test_production_postgres_boot::test_production_runtime_boots_on_postgresql` | Assertion expected schema version 12 but actual is 17 | Verify migration inventory 001–017 and checksums, then correct stale expectation with evidence. |

The PostgreSQL log contains duplicate-constraint exceptions and repeated idempotency-key conflicts during concurrent release tests. These messages must be interpreted with the JUnit outcome and concurrency contract; do not classify them as harmless merely because a unique constraint rejected a duplicate insert.

## 4. Historical 21 SHUUD/SANDBOX failures — separate unresolved set

The prior 21 failures remain a separate register at `docs/FINAL_LOCK_21_FAILURE_DISPOSITION_REGISTER.md`. Their diagnostic source was the earlier `d9c8af8...` run and root-test log (21 failed, 899 passed, 50 skipped). The 14 PostgreSQL regression nodes above are **not** replacements for, or resolutions of, those 21 SHUUD/SANDBOX failures. Product-scope exclusion from EAI does not equal a fix or an approved waiver. All 21 remain OPEN until individually rerun or explicitly dispositioned by an accountable reviewer.

## 5. SHA and evidence integrity

- The a66c134 Production Gate manifest binds candidate commit, checkout head and PR head consistently; its 681/681 source hashes are complete.
- Its status is nevertheless `INCOMPLETE_OR_FAILED`, with 7 gate-file failures and nonzero JUnit failures/errors.
- The earlier `d9c8af8...` re-performance artifact `12457545216` embeds `e872ba14c40be0904260308e626aaab8d0a4c6f7` instead of its declared run head; it remains quarantined and must not be rewritten in place.
- New evidence must be generated from one frozen SHA; require `expected_sha == github_sha == checked_out_sha == tested_commit`, matching migration inventory/checksums, complete source hashes, clean checkout, and retained JUnit/logs.

## 6. Remaining production requirements

No sufficient SHA-bound proof was established in this audit for all of the following:

1. IAM/MFA, privileged access control and access review.
2. Legacy authority-store write freeze and proof that no legacy source can authoritatively write.
3. Observability, alerting, recovery/restart and no-duplicate-value-movement evidence.
4. Production-like load, concurrency, contention and performance acceptance.
5. Backup/restore, disaster recovery and post-restore reconciliation.
6. Release governance, immutable evidence index and accountable independent approval.
7. Complete independent re-performance of all mandatory gates on the same frozen candidate SHA.

## 7. Required next actions

1. Preserve the exact JUnit node IDs above and the historical 21-node register; do not merge or discard either set.
2. Resolve the duplicate CHECK-constraint replay defect and investigate the smoke-test lock timeout with PostgreSQL lock diagnostics.
3. Fix the value-flow missing-record defect, align the schema-version assertion to verified migrations 001–017, and restore the required SHUUD boundary-test contract.
4. Account for all seven Production Gate file failures using their exact per-file logs; rerun broad Production Gate and core-gates to completion on one immutable SHA.
5. Regenerate all re-performance, migration, source-hash, independent-audit and PostgreSQL lifecycle artifacts on that same SHA; quarantine any SHA-mismatched artifact.
6. Complete all operational/security controls and obtain an explicit authorized decision.

**No production-ready certification or final lock is granted by this audit.**
