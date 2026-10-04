# EA-35 PostgreSQL production re-performance evidence

This document is a release-gate record, not a pass declaration.

## Required evidence
- Exact branch/commit under test.
- PostgreSQL 16 service.
- Canonical migrations 001–007 applied with ON_ERROR_STOP.
- ProductionRuntimeFactory construction.
- production_entrypoint controlled boot.
- Canonical FUND → LOCK → RELEASE.
- RELEASE replay/idempotency.
- REFUND and CANCEL.
- Deep value-truth reconciliation.
- Canonical value-flow tests.
- Exact GitHub Actions result attached to the tested commit.

## Current gate
Status: IN PROGRESS / NOT LOCKED.

A GitHub Actions run is required before this document can be used as production evidence.


## Verified failure analysis — 2026-10-04
The exact-SHA workflow evidence previously observed showed two blockers on an older branch snapshot: PostgreSQL concurrency reported duplicate schema_version version 2 publication, and core-gates reported a SyntaxError caused by literal escaped newline sequences in services/gerchain_runtime.py. Subsequent branch state contains migration serialization/idempotency hardening and the runtime syntax correction. These fixes require a fresh exact-SHA workflow result before they can be considered verified.
