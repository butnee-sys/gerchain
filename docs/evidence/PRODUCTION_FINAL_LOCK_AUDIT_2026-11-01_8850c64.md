# Production Final-Lock Evidence Audit — 2026-11-01 — candidate 8850c6488ad11930488b62c9d1b7a6c7ccaadb74

**Decision:** `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.
**Repository / branch:** `butnee-sys/gerchain` / `fix/withdraw-unverified-production-certificate`
**Candidate SHA:** `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`
**PR:** [#111](https://github.com/butnee-sys/gerchain/pull/111), still draft/open at review.
**Purpose:** reconcile current exact-SHA workflow evidence, the historical 21-test register, SHA-mismatched artifacts, and outstanding Master Gate controls. This is an evidence review, not release approval.

## 1. Exact-SHA workflow evidence

All workflow runs listed below report candidate head SHA `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`, attempt 1, and completed success:

| Gate | Run / artifact | Result and bounded interpretation |
|---|---|---|
| Production Gate | [41283229336](https://github.com/butnee-sys/gerchain/actions/runs/41283229336) / artifact [13073608390](https://github.com/butnee-sys/gerchain/actions/runs/41283229336/artifacts/13073608390) | `PASS_CANDIDATE`; 681 source files hashed, no missing files; 313 JUnit files/suites, 0 failures, 0 errors, 18 skipped; file failure count 0. |
| Production PostgreSQL Gate | [41283229283](https://github.com/butnee-sys/gerchain/actions/runs/41283229283) / artifact [13074725186](https://github.com/butnee-sys/gerchain/actions/runs/41283229283/artifacts/13074725186) | `PASS_CANDIDATE`; exact SHA match; 17/17 migrations, matching SHA-256 and history; 13/13 source hashes complete; source worktree clean; lifecycle JUnit 6/6, 0 failures/errors/skips. |
| core-gates | [41283229268](https://github.com/butnee-sys/gerchain/actions/runs/41283229268) / artifact [13074576074](https://github.com/butnee-sys/gerchain/actions/runs/41283229268/artifacts/13074576074) | Success; EAI scope manifest has complete source hash inventory; its JUnit scope report is retained. |
| EAI PostgreSQL Re-performance | [41283229290](https://github.com/butnee-sys/gerchain/actions/runs/41283229290) / artifact [13074167648](https://github.com/butnee-sys/gerchain/actions/runs/41283229290/artifacts/13074167648) | Success; core JUnit 56/56 and deep reconciliation JUnit 24/24, no failures/errors/skips. |
| PostgreSQL Production Re-performance | [41283229289](https://github.com/butnee-sys/gerchain/actions/runs/41283229289) / artifact [13074031998](https://github.com/butnee-sys/gerchain/actions/runs/41283229289/artifacts/13074031998) | `PASS_CANDIDATE`; `github_sha == checked_out_sha == tested_commit == 8850c6488ad11930488b62c9d1b7a6c7ccaadb74`; production boot evidence present; all 17 migrations recorded. Reconciliation is explicitly an empty-baseline report (0 movements/witnesses/outbox/idempotency/escrow rows), not a populated production transaction graph. |
| SHUUD/SANDBOX Product MVP | [41283229307](https://github.com/butnee-sys/gerchain/actions/runs/41283229307) / artifact [13074212633](https://github.com/butnee-sys/gerchain/actions/runs/41283229307/artifacts/13074212633) | Product JUnit 108 passed, 0 failures, 0 errors, 0 skips. Both ordinary and PostgreSQL process-restart tests passed. Separate product scope; not an EAI production certificate. |
| Independent Production Audit | [41283229297](https://github.com/butnee-sys/gerchain/actions/runs/41283229297) / artifact [13073579731](https://github.com/butnee-sys/gerchain/actions/runs/41283229297/artifacts/13073579731) | Workflow success; audit verdict says automated evidence only, not production-ready certification or independent authorized sign-off. |
| FINAL EAI/CORE Exact-SHA Gate | [41283229233](https://github.com/butnee-sys/gerchain/actions/runs/41283229233) | Success on the same SHA. |
| PostgreSQL Production Gate | [41283229239](https://github.com/butnee-sys/gerchain/actions/runs/41283229239) | Success on the same SHA. |
| CodeQL Advanced | [41283229276](https://github.com/butnee-sys/gerchain/actions/runs/41283229276) | Success on the same SHA. |
| CI Test Suite | [41283229323](https://github.com/butnee-sys/gerchain/actions/runs/41283229323) | Success on the same SHA. |
| PostgreSQL concurrency/migration | [41283229326](https://github.com/butnee-sys/gerchain/actions/runs/41283229326) | Success on the same SHA; scoped to its workflow's checks. |

### Skipped tests are not silently counted as PASS

The broad EAI regression JUnit contains 1,212 cases, 0 failures, 0 errors, and 18 skipped. The retained skip reasons include missing `GERCHAIN_TEST_POSTGRES_URL`, `GERCHAIN_TEST_PRODUCTION_DATABASE_URL`, `TEST_POSTGRES_URL`, and `DEE_POSTGRES_URL`. Dedicated PostgreSQL lifecycle/re-performance workflows cover some related cases, but the skipped broad-suite cases remain explicitly skipped in that JUnit. In particular, the broad job does not establish the DEE PostgreSQL concurrent-rotation case. Do not relabel the 18 skips as passed.

## 2. Historical 21-failure reconciliation

The prior diagnostic at `d9c8af8...` recorded 21 failures (20 SHUUD product tests plus one workflow-boundary contract). On `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`:

- Historical rows #2–#21 each have a corresponding passing test case in the isolated SHUUD/SANDBOX Product MVP JUnit (108 passed, no skips).
- Historical row #1's old path-isolation assertion was superseded by the explicit manual-entrypoint/boundary contract. Production Gate per-file JUnit `tests__test_final_lock_contract.py.junit.xml` records 5/5 passing, including `test_shuud_workflows_are_separate_manual_entrypoints` and `test_core_gate_excludes_shuud_product_tests_but_keeps_boundary_tests`.
- This is test-level resolution for the historical cases on this exact SHA, not a SHUUD production-release approval. The old #1 assertion is a replacement contract, not the same test node.
- The detailed one-to-one mapping is appended to `docs/FINAL_LOCK_21_FAILURE_DISPOSITION_REGISTER.md`.

## 3. Independent SHA-256 re-computation

The PostgreSQL lifecycle report records 17 migration hashes and 13 source-file hashes, with `source_hashes_complete=true`, `source_missing=[]`, `source_worktree_clean=true`, `migration_checksums_match_files=true`, `migration_checksums_sha256_valid=true`, and exact candidate/checkout/tested SHA equality.

For this review, the 17 migration files and all 13 listed source files were fetched from GitHub at ref `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`; SHA-256 was independently recomputed over each retrieved file's UTF-8 content and compared with the report. **All 30/30 comparisons matched.** The migration history artifact also records contiguous versions 1–17 and applied timestamps. This validates those 30 listed files; it is not a second independent re-hash of all 681 files in the Production Gate manifest.

## 4. Historical SHA mismatch disposition

Artifact `12457545216` from old run `39849400050` embeds `e872ba14c40be0904260308e626aaab8d0a4c6f7`, not the run's declared `d9c8af8...` head. It remains quarantined and immutable. It is not included in the current evidence set. The replacement PostgreSQL production re-performance artifact for this checkpoint is `13074031998`, which binds its embedded run ID and all tested SHA fields to `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`. Do not rewrite the old artifact in place.

## 5. MG-07 through MG-14 — evidence review

| Gate | Evidence examined | Current disposition |
|---|---|---|
| MG-07 Legacy authority freeze | `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md` says implemented/not locked and explicitly says physical legacy stores are not yet proven read-only/removed. | **OPEN** — require physical/read-only or removal proof and negative write tests on the deployed production boundary. |
| MG-08 IAM/MFA and privileged access | E-GOV-001 README records owner assertions and an access review dated 2026-10-08; CORE audit index says independent settings/screenshot re-performance is open and privileged-access review evidence is missing. | **OPEN / PARTIAL** — obtain current machine-verifiable enforcement and privileged-access review, independently checked. |
| MG-09 Observability/recovery | E-GOV-002 describes logs and health scripts, but no current-SHA retained alerting, readiness, incident, restart and no-duplicate-movement operational bundle was established. PostgreSQL lifecycle tests are bounded technical evidence only. | **OPEN** — supply live operational telemetry/alerts and recovery/restart evidence tied to the candidate deployment. |
| MG-10 Performance/concurrency | E-GOV-003 references scripts and PostgreSQL concurrency tests; no reproducible production-like load profile with throughput/latency/error/contended-write acceptance thresholds and retained results was verified. | **OPEN** — run and retain a declared workload/threshold report. |
| MG-11 Backup/restore/DR | E-GOV-004 references a SQLite backup file and bootstrap script; no PostgreSQL backup restore drill with post-restore ledger/reconciliation proof was verified. | **OPEN** — execute a real PostgreSQL restore/DR drill and record measured RPO/RTO plus reconciliation. |
| MG-12 CI/release governance | Exact-SHA workflows above pass, but branch protection/ruleset and required-check policy were not independently verified; branch-protection API access was denied to this integration. | **PARTIAL / UNVERIFIED** — provide repository settings export/screenshot or authorized ruleset evidence and release approval policy. |
| MG-13 Independent re-performance | Automated EAI/PostgreSQL re-performance and automated audit workflows succeed, but audit verdict is not an independent operator's signed acceptance; the production reconciliation snapshot is empty baseline. | **OPEN** — independent operator must reproduce and sign the defined non-empty lifecycle/reconciliation/recovery checks. |
| MG-14 Evidence index and authorized approval | Run-scoped artifacts exist, but the complete cross-gate evidence index and an authorized final decision for this candidate are not present. | **OPEN** — map every mandatory gate to exact-SHA artifact/verifier and obtain explicit authorized sign-off. |

The old `artifacts/ea35/verified-evidence-*.txt` records bind to `c35d459...`, not this candidate, and are not reused as current-SHA proof. The `artifacts/master_v1` bundle/report set targets the older architecture baseline `10a408dc...`; it is not a current release approval.

## 6. Final disposition

- `FINAL LOCK = OPEN`
- `PRODUCTION READY = NOT VERIFIED`
- Production Gate / PostgreSQL lifecycle reports remain `PASS_CANDIDATE`, not final certification.
- Historical 21 test failures have current-SHA test-level pass evidence, with row #1 replaced by a passing boundary contract.
- The 18 broad EAI JUnit skips remain skipped and must not be represented as passes.
- MG-07 through MG-14 remain open or partially evidenced as specified above.
- PR #111 remains draft/open. No certificate is promoted and no final lock is granted.

