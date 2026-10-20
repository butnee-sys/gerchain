# EA-35 Production Verification Gate

Status: IN PROGRESS / NOT LOCKED

This gate binds production verification to one exact source commit. A historical success or a run against a different merge SHA is not current evidence.

## Required evidence tuple

- Source commit SHA
- GitHub Actions run ID and workflow URL
- `core-gates` collection result
- PostgreSQL concurrency and migration-publication result
- Canonical migration inventory: exactly versions 1–16, one canonical file per version
- Per-version source SHA-256 and runner checksum compared with `schema_version`
- Production runtime boot result on disposable PostgreSQL
- Restart/recovery result with ledger movement, witness, outbox, idempotency and account-balance reconciliation
- Archived workflow artifact containing logs and reconciliation report

## Historical failure evidence (not current)

Run `36542458205` (`core-gates`, run number 2905) failed test collection with 9 errors caused by a SyntaxError in `services/gerchain_runtime.py` at line 275: a function body had been committed as literal escaped newline sequences. The exact failing checkout was merge commit `8529dd30f17d8d3d7126796ea7cdf9ca37943661`, which merged `e860f502f3e1a2d56fd873ad2faab7b1ab630740` into `621e7e2acefe243d4c72e783970e1eb833c60b96`.

Run `36542458201` (`PostgreSQL Concurrency`, run number 1618) failed `test_migrations_are_serialized_and_checksum_is_stable`: PostgreSQL reported duplicate `schema_version` primary key for version 2. This is a failed historical observation, not a pass.

## Acceptance criteria

1. The exact source SHA has no SyntaxError and `core-gates` collection reports zero collection errors.
2. PostgreSQL concurrency suite passes on a fresh disposable database; no duplicate `schema_version` publication remains.
3. Migration inventory equals versions 1–16 exactly; each recorded checksum matches an accepted canonical source checksum, with no conflicting rows.
4. Production runtime starts using PostgreSQL and canonical ledger authority, not legacy release or in-memory value authority.
5. Restart/recovery preserves value truth: no duplicate movement, no missing/mismatched witness, no missing/mismatched outbox, no incomplete idempotency, and unchanged expected account totals.
6. All reports/logs are attached as a workflow artifact and reference the same source SHA and run ID.

No acceptance item is considered complete without fresh exact-SHA evidence.