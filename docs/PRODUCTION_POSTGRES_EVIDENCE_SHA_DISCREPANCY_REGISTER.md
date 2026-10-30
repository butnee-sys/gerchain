# Production PostgreSQL Evidence SHA Discrepancy Register

**Disposition: HISTORICAL ARTIFACT INVALID FOR THE CLAIMED RUN SHA; NOT REWRITTEN IN PLACE.**
**Decision: FINAL LOCK = OPEN; PRODUCTION READY = NOT VERIFIED.**

## 1. Mismatched historical artifact

- Workflow run: [39849400050](https://github.com/butnee-sys/gerchain/actions/runs/39849400050), labeled PostgreSQL Production Re-performance.
- Workflow run head SHA: `d9c8af8d7b9498ff6c814543112a06d11f73602b`.
- Artifact: `12457545216`, `production-gate-evidence`.
- Artifact file: `production-gate-evidence.json`.
- Embedded `run_id`: `39849400050` (matches).
- Embedded `github_sha` and `checked_out_sha`: `e872ba14c40be0904260308e626aaab8d0a4c6f7` (do **not** match run head).
- `tested-commit.txt` and `reconciliation-report.json` also identify `e872ba14...`.
- ZIP SHA-256: `2ca5a5aa36cdb3c785578b0e017fb20d8726205a497bff4737d1a38749458449`.

**Disposition:** quarantine artifact 12457545216 as SHA-mismatched. It cannot support any assertion about candidate `d9c8af8...`. The artifact is immutable historical output; “fixing” its JSON after the run would destroy provenance. Preserve it and supersede it with a new run/artifact generated from the intended frozen commit.

## 2. Correct-SHA replacement evidence (limited)

- Workflow: [PostgreSQL Production Re-performance run 40976838988](https://github.com/butnee-sys/gerchain/actions/runs/40976838988).
- Artifact: `12941984507`.
- Candidate SHA in `production-gate-evidence.json`: `d371daa4263be8736e0c2ca782f09cf06f8d02b2`.
- `github_sha == checked_out_sha == d371daa4263be8736e0c2ca782f09cf06f8d02b2`.
- Embedded `run_id` is `40976838988`.
- `evidence_status` is explicitly `COLLECTED_PENDING_VERIFICATION`, **not PASS**.
- Migration history lists versions 1–17. The reconciliation report is an empty-baseline check with zero movement/witness/outbox/idempotency/escrow rows; it is not evidence of a non-empty production transaction lifecycle.
- Replacement ZIP SHA-256: `6ca0a911c9b071de12fab3d309d79e67ca2bad978de00c7cda2ac44c9cfa8be2`.

This replacement corrects the commit-binding discrepancy for its own run. It does not promote the evidence to PASS_CANDIDATE or prove production lifecycle acceptance.

## 3. Missing full-gate evidence

The later [Production PostgreSQL Gate run 40976839116](https://github.com/butnee-sys/gerchain/actions/runs/40976839116) was cancelled while the EAI regression command was running. Its retained artifacts contain only a partial log and no complete JUnit XML or completed lifecycle report. Therefore it cannot establish the full gate's pass/fail totals, complete source-hash coverage, or PostgreSQL lifecycle completion.

## 4. Required closure

1. Freeze one candidate SHA and rerun the complete PostgreSQL production gate with bounded execution that retains complete logs and JUnit on failure/cancellation.
2. Require `expected_sha == github_sha == checked_out_sha == tested_commit == final_commit` in the evidence package.
3. Validate all migration and required source-file hashes, manifest/report sidecars, migration history, constraints, boot and lifecycle reports.
4. Keep `COLLECTED_PENDING_VERIFICATION` distinct from `PASS_CANDIDATE`; never infer a pass from artifact presence or workflow success alone.
5. Bind independent re-performance and all outstanding operational/release controls to that same frozen SHA.

No artifact is silently rewritten, no SHA mismatch is waived, and no certificate is promoted by this record.
