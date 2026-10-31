# Production Gate evidence manifest integrity and failure disposition

**Decision remains: `FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.**  
**This document is a traceability record, not a production certificate or waiver.**

## Candidate and evidence provenance

- Historical diagnostic candidate: `d9c8af8d7b9498ff6c814543112a06d11f73602b`.
- Historical Production PostgreSQL Gate: [run 39849400091](https://github.com/butnee-sys/gerchain/actions/runs/39849400091).
- Diagnostic artifact: `12456362962`; recorded root suite result: **21 failed, 899 passed, 50 skipped**.
- Detailed row-by-row test names, observed causes, requirement boundaries, dispositions, and closure evidence are maintained in [FINAL_LOCK_21_TEST_FAILURE_DISPOSITION_REGISTER.md](../FINAL_LOCK_21_TEST_FAILURE_DISPOSITION_REGISTER.md). This register is authoritative for the individual 21 rows; this document does not replace or silently waive them.

## The 21 historical failures — disposition snapshot

| Rows | Test group / failure class | Requirement affected | Evidence and current disposition |
|---|---|---|---|
| 1 | `test_final_lock_contract.py::test_shuud_workflows_are_path_isolated` — expected path filter differs from actual workflow trigger policy | CI workflow isolation and EAI/SHUUD boundary | **OPEN**. Must be reconciled with the approved trigger policy and pass a contract test or receive explicit authorized policy approval. |
| 2–3, 15–17, 19 | SHUUD lifecycle and measurement tests — non-monotonic operational timestamps | Lifecycle chronology, measurement correctness, validation ordering | Historical failure observed. Matching tests later passed on candidate `2c4c6dd0871a688e4f3f7dc354295020d2a5da8a`; current frozen candidate must still be revalidated. |
| 4 | SHUUD persistence recovery — missing `incident_id` | Canonical incident identity across persistence/state loss | Matching test later passed on `2c4c6dd...`; current-SHA revalidation required. |
| 5–6 | SHUUD app route inspection — FastAPI `_IncludedRouter.path` attribute error | Route registration and static mount ordering | Matching tests later passed on `2c4c6dd...`; current-SHA revalidation required. |
| 7 | SHUUD DEE proof — unprotected DEE release path | Root-of-trust path protection | Matching test later passed on `2c4c6dd...`; separate DEE Security Gate still requires its own evidence. |
| 8–12 | SHUUD economics validation — missing required keyword-only inputs | Complete/paired economic input validation | Matching parameter cases later passed on `2c4c6dd...`; current-SHA revalidation required. |
| 13–14 | SHUUD KPI integrity — expected canonical snapshot count 1, observed 0 | Persisted snapshot aggregation and no-double-count update | Matching tests later passed on `2c4c6dd...`; current-SHA revalidation required. |
| 18 | SHUUD economic-input validation masked by timestamp-order error | Validation precedence and complete economic inputs | Matching test later passed on `2c4c6dd...`; current-SHA revalidation required. |
| 20 | SHUUD real-process restart E2E — HTTP 404 | Persisted-resource route after restart | Matching historical test passed on `2c4c6dd...`; a separate PostgreSQL restart E2E remained skipped because `SHUUD_POSTGRES_DSN` was absent. |
| 21 | SHUUD sandbox config — missing `SandboxConfig.status` constructor argument | Sandbox configuration contract | Matching test later passed on `2c4c6dd...`; current-SHA revalidation required. |

### Later evidence is not blanket closure

The separate SHUUD/SANDBOX workflow run [41029048996](https://github.com/butnee-sys/gerchain/actions/runs/41029048996), artifact `12965650542`, at candidate `2c4c6dd0871a688e4f3f7dc354295020d2a5da8a`, reported 108 tests: 107 passed, 0 failed, 0 errors, 1 skipped. A node-ID cross-check showed rows #2–#21 passing on that SHA. Row #1 was not in that JUnit and remains open. The skipped PostgreSQL process-restart test is an additional outstanding SHUUD check. Because the branch has advanced, none of this is a substitute for rerunning the relevant checks on the final frozen candidate SHA.

## SHA-mismatched artifact quarantine

PostgreSQL Production Re-performance run [39849400050](https://github.com/butnee-sys/gerchain/actions/runs/39849400050), artifact `12457545216`, contains `migration-catalog-proof.json`, `production-gate-evidence.json`, and `tested-commit.txt` bound to `e872ba14c40be0904260308e626aaab8d0a4c6f7`. The run metadata and companion candidate evidence identify `d9c8af8d7b9498ff6c814543112a06d11f73602b`. **This artifact is quarantined and is not admissible as evidence for either SHA until its run-attempt provenance is reconciled.** Do not rewrite its embedded SHA or relabel it as candidate evidence.

A separate canonical migration run on 2026-10-30 also exposed the GitHub synthetic pull-request merge SHA versus PR-head SHA distinction. Commit `644b2302eab3fda1e3446130f90767c6560b64b5` corrected the canonical migration workflow to checkout and bind evidence to `github.event.pull_request.head.sha || github.sha`. Its rerun must still prove exact equality in the retained artifact.

## Production Gate JSON generator correction

The per-file Production Gate previously incremented a shell-local `failures` counter for database-reset failures and test-file failures, but the later JSON-manifest step did not consume that counter. Consequently, a manifest could report `PASS_CANDIDATE` based only on the JUnit subset even when the shell gate had recorded a per-file failure without a JUnit file.

The workflow correction:
1. Writes the final shell counter to `artifacts/production-gate/file-failure-count.txt`.
2. Reads that value when creating `canonical-evidence-manifest.json`; missing or malformed count is fail-closed (`-1`).
3. Includes `gate_file_failure_count` in the JSON report.
4. Allows `PASS_CANDIDATE` only when the canonical and checked-out SHAs match, at least one JUnit exists, the shell failure count is exactly zero, JUnit failures/errors are zero, and all tracked source hashes are complete.

This is a correction to evidence classification, not a claim that the tests pass. The new workflow run and generated JSON artifact must be inspected on the new commit before this correction is considered verified.

## Same-SHA closure requirements

- Preserve the raw workflow logs, complete JUnit XML, JSON manifest, source-file SHA-256 inventory, and PostgreSQL migration history as downloadable artifacts.
- Verify `canonical_commit_sha`, `commit_sha`, `checked_out_head_sha`, PR-head SHA, workflow run ID, and attempt against the exact candidate commit.
- Reconcile the quarantined `e872ba14...` artifact from source run metadata; never merge mismatched evidence.
- Re-run the 21 individual test node IDs. Close a row only with same-SHA passing JUnit/log evidence, or an explicit, reviewable scope decision by the responsible authority. Product-scope exclusion must not be described as a passing test.
- Complete independent re-performance and the outstanding production controls: legacy-authority write-freeze, IAM/MFA, observability/recovery, performance/concurrency, backup/restore/DR, CI/release governance, and final authorized approval.

Until all conditions are evidenced on one frozen SHA: **`FINAL LOCK = OPEN`; `PRODUCTION READY = NOT VERIFIED`.**
