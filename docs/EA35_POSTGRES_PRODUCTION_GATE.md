# EA-35 PostgreSQL Production Gate

Status: IN PROGRESS / NOT LOCKED

This gate is satisfied only by fresh PostgreSQL execution evidence tied to the exact candidate commit. Source inspection alone is not execution evidence.

## Required acceptance checks

1. Run the canonical migration runner twice against the same clean PostgreSQL database.
2. After each run, assert that schema_version contains exactly versions 1 through 13, each version appears once, and each recorded checksum is stable.
3. Snapshot version/checksum rows after run one and prove run two leaves them unchanged.
4. Construct ProductionRuntimeFactory with a PostgreSQL engine and assert is_canonical_ledger_authoritative is true; reject non-PostgreSQL URLs.
5. Seed or execute a canonical value-flow graph in PostgreSQL and require deep_reconcile_value_truth(session).matched == true.
6. Include a concurrent migration-runner test proving one schema_version publication per version, without swallowing conflicting checksums.
7. Preserve logs and test results for the exact commit SHA.

## Known evidence and limitations

- A PostgreSQL Concurrency run on 2026-10-08 failed in test_migrations_are_serialized_and_checksum_is_stable: duplicate key on schema_version version 2. That is a blocking historical failure, not a pass.
- The current migration runner source contains session-scoped advisory serialization and INSERT ... ON CONFLICT (version) DO NOTHING with checksum verification. This source-level hardening does not replace a fresh successful rerun.
- The production factory must be verified with a real PostgreSQL service; SQLite-only tests do not satisfy this gate.
- No production lock is permitted while any required check is unverified or failing.

## Lock decision

Production status remains IN PROGRESS / NOT LOCKED until all required checks pass on one exact candidate SHA and independent re-performance is recorded.
