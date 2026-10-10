# EA-35.50 — Canonical PostgreSQL Migration Evidence Bundle

Status: IN PROGRESS / NOT LOCKED. This document defines the evidence collected by `.github/workflows/canonical-postgres-gate.yml`; it does not claim a passing run.

## Required release evidence

1. Exact commit SHA and workflow run ID/attempt.
2. Fresh isolated PostgreSQL database, two independent migration connections, and exactly versions 1 through 13.
3. A second full migration pass with identical `(version, checksum)` rows.
4. SHA-256 for every SQL file under `postgres/migrations/`.
5. Production schema validation for required tables, columns, lifecycle state CHECK, named canonical CHECK constraints, and uniqueness requirements.
6. Captured test logs plus the manifest in the `canonical-postgres-evidence-<commit SHA>` Actions artifact.

## Canonical schema contract currently enforced

- Tables: `schema_version`, `escrows`, `gerchain_ledger_accounts`, `gerchain_ledger_movements`, `gerchain_transaction_witnesses`, `gerchain_outbox_events`, `gerchain_idempotency_records`.
- `escrows`: canonical lifecycle states CREATED, FUNDED, LOCKED, RELEASED, REFUNDED, CANCELLED; positive amount; currency and refund destination required; canonical party and timestamp fields.
- Ledger: account balance non-negative; movement source and destination distinct; transaction identifier unique.
- Witness: transaction identifier unique and event type constrained to supported GerChain value/state events.
- Outbox: event identifier unique and state constrained to PENDING, PROCESSING, COMPLETED, FAILED.
- Idempotency: key unique and fingerprint length 64.

## Known validation boundary

The production validator verifies the required tables/columns and named CHECK constraints, and verifies key uniqueness constraints. It does not yet claim exhaustive semantic validation of every foreign key, index, trigger, privilege, or deployment-specific PostgreSQL setting. Any such requirements discovered by schema inspection must be recorded as separate gaps before production lock.

## Artifact contents

- `manifest.json`: exact source commit, workflow run metadata, Python version, and SHA-256/byte length of each migration SQL file.
- `commit-sha.txt`: exact source commit.
- `logs/migration-concurrency.log`: clean-database versions 1–13 and rerun checksum comparison.
- `logs/migration-publication-integrity.log`: duplicate publication and checksum fail-closed cases.
- `logs/production-entrypoint.log`: entrypoint contract tests.
- `logs/deep-value-reconciliation.log`: PostgreSQL deep reconciliation tests.

## Closure rule

Do not mark GREEN or LOCKED unless the exact-SHA Canonical PostgreSQL production gate completes successfully, its artifact is available, all versions 1–13 are present exactly once, the second migration pass leaves schema-version checksums unchanged, and no required schema gap remains unresolved.