# EA-35 / EAI Workflow and Evidence Catalog

**Branch audited:** `feat/ea21-transaction-aware-ledger`  
**Audit date:** 2026-10-10  
**Purpose:** Establish one index for the overlapping EA-35 PostgreSQL production, re-performance, exact-SHA, and EAI evidence records. This catalog is an inventory and routing policy; it does not itself certify a release.

## Audit finding

The documentation directory contains **65 files** whose names match EA35, EAI, PostgreSQL, production evidence, or exact-SHA evidence patterns. The workflow directory contains multiple PostgreSQL/value-truth workflows with overlapping triggers and checks. This is evidence of duplicated documentation/workflow intent, not proof that every file is redundant.

## Canonical authority order

Use these files as the active entry points:

1. `docs/EA35_EXACT_SHA_EVIDENCE_INDEX.md` — single index of evidence items and their status.
2. `docs/EA35_EXACT_SHA_EVIDENCE_STATUS.md` — latest audited SHA and exact-SHA gate decision; update only after inspecting current Actions results.
3. `docs/EA35_DEEP_VALUE_TRUTH_CONTRACT.md` — invariant/acceptance contract.
4. `docs/EA35_EAI_PRODUCTION_GATE.md` — EAI scope and lock criteria.
5. `docs/EA35.13_POSTGRESQL_REPERFORMANCE_PROTOCOL.md` — procedure for real PostgreSQL re-performance.
6. `docs/EA35_FINAL_EVIDENCE_MANIFEST.md` — final artifact manifest, populated only after runs complete.
7. `docs/EA35_FINAL_LOCK_READINESS.md` — readiness decision; not an independent evidence source.

The documents above must refer to the same immutable commit SHA before a lock decision. A narrative status in one document must not override fresh GitHub Actions results.

## Workflow roles

### Keep as the intended authoritative gate
- `.github/workflows/canonical-postgres-gate.yml` — canonical runtime boot, schema presence, and deep value-truth suite.
- `.github/workflows/ea35-postgres-reperformance.yml` — PostgreSQL re-performance and factory boot.
- `.github/workflows/ea35-value-truth-postgres.yml` — PostgreSQL-specific value-truth test.
- `.github/workflows/final-exact-sha-full-suite.yml` — full-suite evidence on the exact pushed/PR SHA.
- Existing security and CORE gates remain separate controls; they are not substitutes for PostgreSQL production proof.

### Consolidation rule
These PostgreSQL workflows currently overlap in PostgreSQL service setup, Python setup, dependency installation, factory/schema verification, and deep value-truth tests. Do not add another workflow for the same purpose. The next workflow change should consolidate duplicate execution into one authoritative PostgreSQL production gate with named jobs/steps for:
1. migration/bootstrap and concurrency;
2. production entrypoint boot and canonical authority;
3. durable value-flow/replay;
4. deep value-truth reconciliation;
5. independent persisted-state verification;
6. artifact upload and exact-SHA manifest.

Until consolidation is reviewed and the replacement is passing, do not delete or disable the existing workflows.

## Historical evidence files

Files whose names contain dates, `EVIDENCE`, `STATUS`, `LOCK`, `PROOF`, `GATE`, or `REPERFORMANCE` are not automatically interchangeable. Preserve them as historical records unless their contents are compared and their run IDs/SHA are captured in the active index. Do not mass-delete based on filename similarity.

## Known integrity hazard

Some historical EAI evidence files record earlier SHAs and successful run IDs, while the current exact-SHA status document records a later SHA with queued/pending runs. A successful run on an older SHA is valid historical evidence but cannot certify the current tip.

**Lock invariant:** the production gate, independent re-performance, full-suite status, and evidence manifest must all identify the same exact SHA and completed successful runs. Missing, queued, stale, or mismatched evidence means **NOT LOCKED**.

## Next cleanup sequence

- [ ] Capture current branch tip SHA.
- [ ] Query current Actions runs for that SHA and record status/conclusion/job IDs.
- [ ] Reconcile each active evidence document against those live results.
- [ ] Mark stale documents explicitly as historical/superseded, retaining their run IDs and SHAs.
- [ ] Consolidate overlapping PostgreSQL workflows after comparing their unique test coverage.
- [ ] Ensure one exact-SHA manifest points to logs/artifacts for each required control.
- [ ] Re-run all required gates after the final cleanup commit; do not reuse pre-cleanup results as proof of the new SHA.

**Current decision:** inventory confirmed; consolidation planned; no evidence deleted; no production lock declared.
