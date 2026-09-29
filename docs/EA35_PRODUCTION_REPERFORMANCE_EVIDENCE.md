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
