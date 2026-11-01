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


## Current branch-head artifact review — 2026-10-30 — SHA 2c4c6dd0871a688e4f3f7dc354295020d2a5da8a

The old artifact 12457545216 remains quarantined and immutable; it is not edited in place. Its embedded `e872ba14...` tested SHA does not match the older run's declared head SHA, so it remains inadmissible for that candidate.

A newer artifact was collected from [PostgreSQL Production Re-performance run 41029049024](https://github.com/butnee-sys/gerchain/actions/runs/41029049024), artifact [12966011382](https://github.com/butnee-sys/gerchain/actions/runs/41029049024/artifacts/12966011382). The archived `production-gate-evidence.json`, `migration-history.json`, `postgres-constraints.json`, and `tested-commit.txt` all identify run 41029049024, attempt 1, and bind `github_sha == checked_out_sha == tested_commit == 2c4c6dd0871a688e4f3f7dc354295020d2a5da8a`. It records migrations 001–017 with applied timestamps and matching migration-file SHA-256 values; all listed PostgreSQL check constraints are validated; production boot reports PASS.

Important limitations: this artifact's top-level `evidence_status` is **COLLECTED_PENDING_VERIFICATION**, not PASS_CANDIDATE. Its reconciliation report is explicitly an empty-baseline reconciliation (zero movements, witnesses, outbox, idempotency, and escrow rows); it is not evidence of a non-empty production transaction history. The artifact itself does not supply a full source-file hash inventory or a lifecycle JUnit report.

The separate [EAI PostgreSQL Re-performance run 41029049038](https://github.com/butnee-sys/gerchain/actions/runs/41029049038), artifact 12965980648, binds commit/expected/tested/final SHA to 2c4c6dd0871a688e4f3f7dc354295020d2a5da8a; its SHA256SUMS manifest is retained, and its JUnit reports core 56/56 and deep reconciliation 24/24 passing. This is scoped EAI evidence, not a substitute for the complete Production PostgreSQL Gate evidence manifest.

At the time of this addendum, [Production PostgreSQL Gate 41029049056](https://github.com/butnee-sys/gerchain/actions/runs/41029049056) and [Production Gate 41029049063](https://github.com/butnee-sys/gerchain/actions/runs/41029049063) remained in progress, while [core-gates 41029049010](https://github.com/butnee-sys/gerchain/actions/runs/41029049010) was pending. Their final logs/JUnit and a complete SHA-bound production evidence bundle remain required.

The new evidence does not rewrite or rehabilitate the historical mismatched artifact, and it does not change the decision:
- `FINAL LOCK = OPEN`
- `PRODUCTION READY = NOT VERIFIED`


## Current exact-SHA replacement evidence — 2026-11-01 — `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`

The earlier artifact `12457545216` remains quarantined and immutable; its embedded `e872ba14...` SHA does not match the old run head. It is excluded from this current evidence set.

Correct-SHA artifacts collected and inspected:

- Production Gate run 41283229336 / artifact 13073608390: `commit_sha == checked_out_head_sha == pull_request_head_sha == 8850c6488ad11930488b62c9d1b7a6c7ccaadb74`; `evidence_status=PASS_CANDIDATE`; 681 source files, no missing source files; JUnit 313 suites, 0 failures/errors, 18 skipped; gate-file failure count 0.
- Production PostgreSQL Gate run 41283229283 / artifact 13074725186: `commit_sha == checked_out_head_sha == tested_commit == 8850c6488ad11930488b62c9d1b7a6c7ccaadb74`; `evidence_status=PASS_CANDIDATE`; 17/17 migrations; 13/13 source hashes complete; clean source worktree; lifecycle JUnit 6/6.
- EAI PostgreSQL Re-performance run 41283229290 / artifact 13074167648: commit and final SHA equal `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`; core 56/56 and deep reconciliation 24/24.
- PostgreSQL Production Re-performance run 41283229289 / artifact 13074031998: `github_sha == checked_out_sha == tested_commit == 8850c6488ad11930488b62c9d1b7a6c7ccaadb74`; `evidence_status=PASS_CANDIDATE`. Its reconciliation report is an empty-baseline check and must not be described as a populated production transaction graph.
- Independent Production Audit run 41283229297 / artifact 13073579731: automated audit success bound to `8850c6488ad11930488b62c9d1b7a6c7ccaadb74`; its verdict explicitly says this is not production-ready certification or independent sign-off.

The 17 migration and 13 source files listed in the PostgreSQL lifecycle report were separately fetched at ref `8850c6488ad11930488b62c9d1b7a6c7ccaadb74` and SHA-256 recomputed. All 30/30 matched the artifact's hashes. The broad EAI regression JUnit still has 18 environment-gated skips; see the 2026-11-01 evidence audit for exact skip reasons and remaining controls.

**This replacement corrects the prior SHA-binding gap for the listed artifacts only. It does not close MG-07–MG-14 or grant FINAL LOCK.**
