# EA-35 Gate A–E — Exact-SHA Production Evidence Contract

Status: IN PROGRESS / NOT LOCKED  
Scope: canonical fundamental architecture + EAI / Canonical Ledger production path. Product layers are excluded.  
Rule: every gate result must identify the same full Git commit SHA. Results from different commits may not be combined into a release claim.

## Gate A — Canonical PostgreSQL migration
Required evidence:
- fresh disposable PostgreSQL database;
- canonical migration inventory is unique and complete;
- two independent PostgreSQL connections race migration publication;
- one authoritative schema_version row per version, identical checksums;
- repeat application is idempotent;
- migration inventory/history report uploaded as an artifact.
Pass only when the exact-SHA workflow job succeeds and its artifact is inspectable.

## Gate B — Production factory and entrypoint
Required evidence:
- production factory boots against PostgreSQL using the canonical runtime;
- canonical ledger authority is asserted;
- missing/non-PostgreSQL configuration fails closed;
- runtime source compiles;
- the entrypoint is exercised in a disposable PostgreSQL service, not only mocked.
Pass only when the exact-SHA integration tests succeed.

## Gate C — Canonical architecture and transaction correctness
Required evidence:
- canonical boundary / adapter / G3 / NEF-GERCHAIN tests;
- one transaction boundary for canonical value movement, escrow state, witness, outbox, and durable idempotency;
- FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, and READ paths tested against PostgreSQL where applicable;
- replay, conflicting replay, rollback, concurrency, and forbidden legacy-path tests.
Pass only when all selected architecture-gate tests succeed on the exact SHA.

## Gate D — Full repository regression
Required evidence:
- full repository pytest suite executes on the same exact SHA as Gates A–C and E;
- no collection errors, failures, or unreviewed skips affecting the release scope;
- workflow result and job logs retained.
A partial test selection is not a substitute for this gate.

## Gate E — Deep value-truth reconciliation and recovery
Required evidence:
- clean movement ↔ escrow ↔ witness ↔ outbox ↔ idempotency graph;
- negative tests detect missing, mismatched, orphaned, or integrity-invalid evidence;
- state-only operations are not falsely classified as value movements;
- recovery/restart re-performance proves no duplicate value movement;
- evidence report and migration inventory artifact refer to the same SHA.
Pass only when PostgreSQL re-performance and recovery tests succeed and their evidence is reviewed.

## Final lock rule
PRODUCTION READY and FINAL LOCK may be issued only after Gates A, B, C, D, and E all pass on one identical full commit SHA; the commit SHA, workflow run URL, job results, and required artifacts must be recorded here or in the release evidence index. Any failure, missing artifact, stale result, unknown result, or cross-SHA evidence keeps the status IN PROGRESS / NOT LOCKED.

## Current observed blockers
- Historical PostgreSQL concurrency workflow logs show duplicate publication of schema_version version 2. This historical failure must be superseded by a fresh exact-SHA passing run, not merely by source inspection.
- Historical core-gates logs include collection failures from an older source snapshot. A fresh exact-SHA passing run must supersede that result.
- No final lock is asserted by this document.
