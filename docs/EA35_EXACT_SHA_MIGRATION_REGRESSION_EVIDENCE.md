# EA-35 — Exact-SHA Migration and CORE Regression Evidence

Status: PENDING — NOT LOCKED

Purpose: preserve migration concurrency, rerun/idempotency, schema checksum, production PostgreSQL boot, and CORE regression results against one exact Git commit without changing the existing production-readiness gate.

## Immutable evidence requirements

The existing `.github/workflows/core-gates.yml` is the authoritative combined gate. Do not weaken, skip, or replace its checks to obtain a pass.

A run is acceptable only when all of these identify the same commit:
- GitHub Actions checked-out `HEAD`
- `github.sha` recorded by the workflow
- migration concurrency and duplicate-publication test results
- migration checksum/inventory report
- production PostgreSQL runtime/schema validation
- CORE regression test result
- uploaded artifact names and metadata

## Required test dimensions

1. **Concurrent migration execution:** multiple runners apply the same migration set concurrently; no duplicate version publication and no partial migration state.
2. **Rerun/idempotency:** re-running migrations against the already migrated database succeeds without duplicating schema or migration-history rows.
3. **Schema checksum:** every canonical migration's on-disk checksum matches the persisted migration history; checksum mismatch fails closed.
4. **CORE regression:** canonical architecture, adapter boundaries, transaction-aware Ledger, durable Escrow, Witness, Outbox, idempotency, and deep value-truth reconciliation tests pass.
5. **Evidence binding:** report includes exact commit SHA, run ID/attempt, database version, migration count/checksums, test command outcomes, and artifact references.

## Acceptance rule

PASS only if the exact-SHA workflow run completes successfully and all required artifacts are retained. Missing checks, missing artifacts, stale runs, SHA mismatch, or any failed test means NOT PASS. Do not declare production lock based on source inspection or a different commit's CI result.

## Current evidence

No new exact-SHA combined-gate result or artifact has been verified for this evidence record yet. Previously inspected workflow runs from 2026-10-12 include failures in CORE regression and PostgreSQL concurrency; those runs are historical signals, not evidence for a newer commit. Their failure logs included a duplicate `schema_version(version=2)` publication race, which is precisely the kind of concurrency condition the gate must prove is resolved.

**Current decision: IN PROGRESS / NOT LOCKED.**
