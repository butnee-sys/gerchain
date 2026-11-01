# Core Gates Runtime Limit and Migration Concurrency Contract

Status: DOCUMENTED — NOT A PRODUCTION-READINESS APPROVAL  
Applies to observed candidate: `d9c8af8d7b9498ff6c814543112a06d11f73602b`  
PR: #111 (draft; documentation-only change)

## 1. Observed six-hour cancellation

### Evidence

- `core-gates`: run `39849400130`, attempt 1, job `124395686582`.
  - Started: 2026-10-31 01:05:01 UTC.
  - Completed: 2026-10-31 07:06:52 UTC.
  - Conclusion: `cancelled`.
  - Last executed required step: `Run full repository test suite on the same commit`.
  - The preceding focused checks passed: workflow YAML, Python compile, PostgreSQL migration publication concurrency regression, and canonical fundamental architecture gate (`92 passed in 7.86s`).
  - The full-suite step began at 01:07 UTC and emitted progress through approximately 16%; it did not complete. The migration inventory audit was skipped.
  - Job log ends with `##[error]The operation was canceled.`

- `Production Gate`: run `39849399966`, attempt 17, job `124395279944`.
  - Started: 2026-10-31 01:04:59 UTC.
  - Completed: 2026-10-31 07:05:23 UTC.
  - Conclusion: `cancelled`.
  - 1,318 tests were collected. The complete test/JUnit step began at 01:05 UTC and emitted progress only through approximately 16%; it did not complete.
  - PostgreSQL migration evidence generation was skipped. The always-run report recorded `evidence_status=BLOCKED`, with `migration-history.json` and `postgres-constraints.json` missing.
  - The master manifest validation step failed closed; the log shows an `AssertionError` because the manifest did not meet its asserted contract.
  - Job log ends with `##[error]The operation was canceled.`

### Assessment

Both jobs ran for approximately six hours before cancellation. Neither workflow declares a job-level `timeout-minutes` in the inspected workflow at the candidate SHA. This timing is consistent with a six-hour hosted-job execution limit. The captured logs show the cancellation but do not identify the platform-side cancellation actor or provide an explicit timeout reason. Therefore record the cause as:

`LIKELY_HOSTED_JOB_SIX_HOUR_LIMIT — timing-supported; platform cancellation reason not explicitly stated in job log.`

Do not record either full-suite result as pass or fail: both are `INCOMPLETE / CANCELLED`. Progress output alone does not identify which individual test was executing at cancellation. Obtain a completed JUnit report or isolated reproductions before assigning root causes to individual tests.

## 2. Migration concurrency contract (#1)

Source of truth:
- Implementation: `postgres/migrations/__init__.py`
- Regression tests: `tests/postgres/test_migration_concurrency.py`
- Workflow step: `Run PostgreSQL migration publication concurrency regression`
- Candidate SHA: `d9c8af8d7b9498ff6c814543112a06d11f73602b`

### Required invariants

1. **Serialization:** competing migration runners acquire the same PostgreSQL session-level advisory lock (key `731946205821`) before publishing migrations. The lock is explicitly released on success and failure.
2. **Atomic publication:** schema DDL, checksum verification, and `schema_version` publication execute within one transaction; the runner requires a clean connection before starting.
3. **Canonical chain:** the production chain is the explicit, contiguous canonical migration sequence 001–017. Duplicate, missing, non-canonical, or unexpected numbered migrations fail closed.
4. **Single publication per version:** `schema_version.version` has a uniqueness invariant. Legacy identical duplicate rows may be collapsed; conflicting checksums for the same version must fail closed and remain available for explicit reconciliation.
5. **Two-runner outcome:** in the isolated-schema concurrency regression, two simultaneous connections must yield exactly one runner applying the full chain and the other applying zero migrations. The union of applied versions must equal the complete expected sequence.
6. **Checksum truth:** each recorded migration checksum must equal the SHA-256 derived from the exact canonical SQL source. A mismatch must fail closed without changing recorded history or schema objects.
7. **Repeat-run idempotency:** a second bootstrap must apply no migrations and must leave version, checksum, and `applied_at` history unchanged.
8. **Schema integrity:** the regression verifies a unique version index and exactly one canonical escrow-state CHECK constraint named `escrows_state_canonical_check`.
9. **Isolation:** the concurrency regression uses a uniquely named disposable schema and drops it afterward; it must not mutate the shared `public` schema.

### Evidence and acceptance

- The test file contains direct assertions for the two-runner result, complete version inventory, checksums, uniqueness, and the canonical state constraint.
- At the observed `core-gates` run, the concurrency regression step completed successfully before the full-suite timeout.
- This establishes that the focused regression passed on the candidate SHA in that run. It does not establish full-suite completion, independent re-performance, production traffic safety, or overall production readiness.
- A future final candidate must rerun this regression against a fresh disposable PostgreSQL database and retain its complete test log and result artifact, all bound to the exact candidate SHA.

## 3. Runtime policy for future full-suite runs

- Keep the focused architecture and concurrency checks separate from the full repository suite so their results remain visible even if the full suite stalls.
- Do not increase a timeout merely to convert an incomplete run into a pass. First identify slow or blocked tests using completed, segmented runs and per-test duration output.
- Split the full suite into deterministic, non-overlapping segments with independent JUnit reports and a final aggregator that fails if any segment is missing, cancelled, skipped unexpectedly, or bound to a different SHA.
- Set explicit job/step time limits that fit the available runner ceiling and report timeout as `INCOMPLETE`, never `PASS`.
- Preserve test failures. Any exclusion or quarantine requires a named owner, linked requirement, technical rationale, bounded scope, expiry/review date, and retained evidence; it must not silently reduce required coverage.

## 4. Manifest mismatch — separate blocking defect

At candidate SHA `d9c8af8d7b9498ff6c814543112a06d11f73602b`, `docs/production-master-gate-manifest.json` was fetched from the repository and contained:

- `expected_commit_sha = 5e5193511b47f0815f28a2c6c76fb9f60634b695`
- `checked_out_head_sha = 5e5193511b47f0815f28a2c6c76fb9f60634b695`
- `decision = NOT_LOCKED`
- `gate_outcomes = {}`
- a non-empty `failures` list, including `MANIFEST_SHA_MISMATCH` and missing required gates.

The manifest blob at that candidate was `1ed21cda2a69006d54a37b8cb594f3e8e330ceb9`. It is historical/stale evidence, not a current candidate-SHA manifest. It must not be represented as final evidence. A future manifest must be generated from actual per-gate outcomes and bind its source SHA, checked-out SHA, workflow run ID/attempt, and evidence hashes. `NOT_LOCKED` remains the correct decision until then.

## 5. Current disposition

- `FINAL LOCK = OPEN`
- `PRODUCTION READY = NOT VERIFIED`
- Six-hour cancellation: documented, but exact platform cancellation actor is not present in the logs.
- Full repository suite: incomplete/cancelled; no JUnit completion.
- Migration concurrency contract: documented; focused check passed in the observed run, still requires final-candidate re-performance.
- Master manifest: stale SHA and `NOT_LOCKED`; not accepted as final evidence.
- No application-code change or final-lock authorization is made by this document.
