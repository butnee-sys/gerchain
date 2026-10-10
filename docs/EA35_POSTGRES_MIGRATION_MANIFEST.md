# Canonical PostgreSQL Migration Manifest (EA-35)

Status: **evidence map; migration gate remains IN PROGRESS / NOT LOCKED**.

## Canonical chain

The authoritative migration directory is `postgres/migrations/`. The canonical runner is `postgres/migrations.py`; `postgres/migration_runner.py` is a compatibility re-export and must not implement a second migration path.

| Version | Canonical file selected by the runner |
|---:|---|
| 1 | `001_canonical_production.sql` |
| 2 | `002_canonical_production.sql` |
| 3 | `003_canonical_compatibility.sql` |
| 4 | `004_canonical_value_truth.sql` |
| 5 | `005_canonical_production.sql` |
| 6 | `006_canonical_movement_integrity.sql` |
| 7 | `007_canonical_production_reconciliation.sql` |
| 8 | `008_ea35_idempotency_compat.sql` |
| 9 | `009_canonical_movement_integrity_hardening.sql` |
| 10 | `010_canonical_evidence_constraints.sql` |
| 11 | `011_ea35_canonical_schema_finalization.sql` |
| 12 | `012_canonical_production.sql` |
| 13 | `013_ea35_canonical_schema_hardening.sql` |

The active chain must resolve to exactly versions 1 through 13, once each, in numeric order. The canonical filenames and the selection policy are also asserted by `tests/postgres/test_migrations.py`.

## Historical aliases and duplicate numeric prefixes

The directory intentionally retains earlier files for historical context/compatibility. Current physical duplicate prefixes are 1, 2, 3, 4, and 5. These are not separate active migrations: the runner chooses the exact canonical filename above. A duplicate that cannot be resolved by the explicit preferred filename or a single unambiguous canonical candidate must fail closed; do not sort-and-run every alias.

This policy is deliberately scoped to `postgres/migrations/`. The older `postgres/schema/` directory is not the active migration source for the canonical runner. Tests that inspect that legacy directory must not be mistaken for proof of the active chain.

## Checksum source of truth

1. For each selected migration, the runner reads the exact UTF-8 file text.
2. The current digest is SHA-256 over that exact text: `sha256(sql.encode("utf-8")).hexdigest()`. Newline changes and other byte-level edits therefore change the digest.
3. The runner records the selected file's digest in `schema_version(version, checksum, applied_at)` only after applying that migration in the serialized migration transaction.
4. When a version already exists, its recorded checksum must equal the selected file's digest or a specifically documented compatibility digest in `FROZEN_CHECKSUMS` / `LEGACY_CHECKSUMS`. Those sets preserve known historical installations; they are not permission to add arbitrary digests to bypass a mismatch.
5. A non-accepted mismatch must raise `Migration checksum mismatch for version N`; the transaction must roll back without partial DDL or migration-history mutation.
6. Duplicate `schema_version` rows with identical checksums may be collapsed only by the tested repair path. Conflicting checksums for the same version must fail closed without silently selecting one.

The migration history table is runtime evidence of what a database recorded. The repository migration file is the source for the current digest. Git blob SHA values are not migration SHA-256 checksums and must not be substituted for them.

## Required proof before locking

- [ ] Static manifest resolves exactly versions 1–13 to the canonical filenames above.
- [ ] Duplicate aliases are deterministic; unresolved duplicates fail closed.
- [ ] Exact file digest and accepted historical digest behavior are tested.
- [ ] A changed applied checksum is rejected without schema/history changes.
- [ ] Identical duplicate history is repaired without duplicate version publication; conflicting duplicate history is rejected.
- [ ] Real PostgreSQL CI passes on the exact commit under review.
- [ ] The CI run and commit SHA are recorded as evidence.
- [ ] Independent re-performance is complete.

Until every required item is evidenced, this manifest does not authorize production lock.
